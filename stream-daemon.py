"""
Stream Daemon - Universal streaming-to-social bridge
Monitors streaming platforms and posts to social media
Configuration via .env files and environment variables only
"""

from twitchAPI.twitch import Twitch
from mastodon import Mastodon
from atproto import Client
from googleapiclient.discovery import build
import google.genai
from google.genai import types
import time
import random
import os
import sys
import logging
import requests
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import from modularized package
from stream_daemon.config import get_config, get_bool_config, get_int_config, get_secret
from stream_daemon.models import StreamState, StreamStatus
from stream_daemon.ai import AIMessageGenerator
from stream_daemon.utils import parse_sectioned_message_file
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()
logger.info("Environment variables loaded")


# ===========================================
# STREAMING PLATFORM CLASSES
# ===========================================

class StreamingPlatform:
    """Base class for streaming platforms."""
    
    def __init__(self, name):
        self.name = name
        self.enabled = False
    
    def is_live(self, username):
        """Check if user is live. Returns (is_live, stream_data) tuple."""
        raise NotImplementedError
    
    def authenticate(self):
        """Authenticate with the platform."""
        raise NotImplementedError


class TwitchPlatform(StreamingPlatform):
    """Twitch streaming platform with enhanced error handling and retry logic."""
    
    def __init__(self):
        super().__init__("Twitch")
        self.client = None
        self.client_id = None
        self.client_secret = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
    def authenticate(self):
        """Authenticate with Twitch API with error handling."""
        try:
            self.client_id = get_secret('Twitch', 'client_id', 
                                  secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
                                  secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH',
                                  doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
            self.client_secret = get_secret('Twitch', 'client_secret',
                                       secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
                                       secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH',
                                       doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
            
            if not all([self.client_id, self.client_secret]):
                logger.warning("✗ Twitch credentials not found")
                return False
                
            # Test authentication by creating a client
            async def test_auth():
                client = None
                try:
                    client = await Twitch(self.client_id, self.client_secret)
                    return True
                except Exception as e:
                    logger.error(f"Twitch auth test failed: {e}")
                    raise
                finally:
                    if client:
                        await client.close()
            
            asyncio.run(test_auth())
            self.enabled = True
            self.consecutive_errors = 0
            logger.info("✓ Twitch authenticated")
            return True
            
        except Exception as e:
            logger.error(f"✗ Twitch authentication failed: {e}")
            self.enabled = False
            return False
    
    def is_live(self, username):
        """
        Check if Twitch stream is live with retry logic and error handling.
        
        Returns:
            tuple: (is_live, stream_data) or (False, None) on error
        """
        if not self.enabled or not self.client_id:
            return False, None
        
        # Disable platform temporarily if too many consecutive errors
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.warning(f"⚠ Twitch disabled temporarily due to {self.consecutive_errors} consecutive errors")
            return False, None
            
        try:
            # Run async check synchronously
            async def check_live():
                client = None
                try:
                    client = await Twitch(self.client_id, self.client_secret)
                    
                    # Get user info with timeout protection
                    user_generator = client.get_users(logins=[username])
                    users = []
                    async for user in user_generator:
                        users.append(user)
                    
                    if not users:
                        logger.debug(f"Twitch user '{username}' not found")
                        return False, None
                    
                    user_id = users[0].id
                    
                    # Check stream status
                    stream_generator = client.get_streams(user_id=[user_id])
                    streams = []
                    async for stream in stream_generator:
                        streams.append(stream)
                    
                    live_streams = [s for s in streams if s.type == 'live']
                    
                    if live_streams:
                        stream = live_streams[0]
                        # Return stream data with safe field access
                        stream_data = {
                            'title': getattr(stream, 'title', 'Untitled Stream'),
                            'viewer_count': getattr(stream, 'viewer_count', 0),
                            'thumbnail_url': stream.thumbnail_url.replace('{width}', '1280').replace('{height}', '720') if hasattr(stream, 'thumbnail_url') and stream.thumbnail_url else None,
                            'game_name': getattr(stream, 'game_name', 'Unknown')
                        }
                        return True, stream_data
                    return False, None
                    
                except asyncio.TimeoutError:
                    logger.error(f"Twitch API timeout checking {username}")
                    raise
                except Exception as e:
                    logger.error(f"Error in Twitch async check for {username}: {e}")
                    raise
                finally:
                    if client:
                        try:
                            await client.close()
                        except Exception as e:
                            logger.debug(f"Error closing Twitch client: {e}")
            
            result = asyncio.run(check_live())
            self.consecutive_errors = 0  # Reset on success
            return result
            
        except asyncio.TimeoutError:
            self.consecutive_errors += 1
            logger.error(f"⚠ Twitch API timeout for {username} (consecutive errors: {self.consecutive_errors})")
            return False, None
        except Exception as e:
            self.consecutive_errors += 1
            logger.error(f"⚠ Error checking Twitch/{username}: {e} (consecutive errors: {self.consecutive_errors})")
            return False, None


class YouTubePlatform(StreamingPlatform):
    """YouTube Live streaming platform with enhanced error handling and quota management."""
    
    def __init__(self):
        super().__init__("YouTube")
        self.client = None
        self.channel_id = None
        self.username = None
        self.quota_exceeded = False
        self.quota_exceeded_time = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
    def authenticate(self):
        """Authenticate with YouTube API with error handling."""
        try:
            api_key = get_secret('YouTube', 'api_key',
                                secret_name_env='SECRETS_AWS_YOUTUBE_SECRET_NAME',
                                secret_path_env='SECRETS_VAULT_YOUTUBE_SECRET_PATH',
                                doppler_secret_env='SECRETS_DOPPLER_YOUTUBE_SECRET_NAME')
            self.username = get_config('YouTube', 'username')
            
            # Optional: Channel ID for direct lookup (faster, but username works too)
            self.channel_id = get_config('YouTube', 'channel_id')
            
            if not api_key:
                logger.warning("✗ YouTube API key not found")
                return False
                
            if not self.username:
                logger.warning("✗ YouTube username not configured")
                return False
                
            self.client = build('youtube', 'v3', developerKey=api_key)
            
            # If channel_id not provided, look it up by username/handle
            if not self.channel_id:
                self.channel_id = self._get_channel_id_from_username()
                if not self.channel_id:
                    logger.warning(f"✗ Could not find YouTube channel for username: {self.username}")
                    return False
            
            self.enabled = True
            self.consecutive_errors = 0
            logger.info("✓ YouTube authenticated")
            return True
            
        except Exception as e:
            logger.error(f"✗ YouTube authentication failed: {e}")
            self.enabled = False
            return False
    
    def _get_channel_id_from_username(self):
        """Convert username/handle to channel ID with error handling."""
        try:
            # Ensure username has @ prefix for handle-based lookup
            lookup_username = self.username if self.username.startswith('@') else f'@{self.username}'
            
            # Try modern handle format first (@username)
            try:
                request = self.client.channels().list(
                    part="id",
                    forHandle=lookup_username
                )
                
                response = request.execute()
                if response.get('items'):
                    channel_id = response['items'][0]['id']
                    logger.info(f"✓ Resolved YouTube channel ID: {channel_id}")
                    return channel_id
            except Exception as e:
                logger.debug(f"Handle lookup failed for {lookup_username}: {e}")
            
            # If handle didn't work and original didn't have @, try legacy username
            if not self.username.startswith('@'):
                try:
                    request = self.client.channels().list(
                        part="id",
                        forUsername=self.username
                    )
                    response = request.execute()
                    if response.get('items'):
                        channel_id = response['items'][0]['id']
                        logger.info(f"✓ Resolved YouTube channel ID: {channel_id}")
                        return channel_id
                except Exception as e:
                    logger.debug(f"Username lookup failed for {self.username}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving YouTube channel ID: {e}")
            return None
    
    def is_live(self, username=None):
        """
        Check if a YouTube channel is live with comprehensive error handling.
        
        Args:
            username: Optional username/handle to check. If not provided, uses self.username.
                     Can be in format '@handle' or 'channelname'
                     
        Returns:
            tuple: (is_live, stream_data) or (False, None) on error
        """
        if not self.enabled or not self.client:
            return False, None
        
        # Disable platform temporarily if too many consecutive errors
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.warning(f"⚠ YouTube disabled temporarily due to {self.consecutive_errors} consecutive errors")
            return False, None
        
        # Check if quota was exceeded recently (skip checks for 1 hour to avoid spam)
        if self.quota_exceeded:
            from datetime import datetime, timedelta
            if self.quota_exceeded_time:
                time_since_quota_error = datetime.now() - self.quota_exceeded_time
                if time_since_quota_error < timedelta(hours=1):
                    # Still in cooldown period
                    logger.debug(f"YouTube API quota exceeded, skipping check (cooldown: {60 - time_since_quota_error.seconds // 60} min remaining)")
                    return False, None
                else:
                    # Cooldown expired, try again
                    logger.info("YouTube API quota cooldown expired, resuming checks")
                    self.quota_exceeded = False
                    self.quota_exceeded_time = None
                    self.consecutive_errors = 0
        
        # Determine which channel to check
        channel_id_to_check = None
        
        try:
            if username and username != self.username:
                # Different username provided - need to resolve it
                channel_id_to_check = self._resolve_channel_id(username)
                if not channel_id_to_check:
                    logger.warning(f"Could not resolve YouTube channel ID for: {username}")
                    return False, None
            else:
                # Use the authenticated channel
                channel_id_to_check = self.channel_id
            
            if not channel_id_to_check:
                logger.error("No YouTube channel ID available")
                return False, None
                
        except Exception as e:
            self.consecutive_errors += 1
            logger.error(f"Error resolving YouTube channel: {e}")
            return False, None
            
        try:
            # OPTIMIZED API USAGE (3 units total vs 101 units before!)
            # Old: search().list(eventType=live) = 100 units + videos().list() = 1 unit = 101 total
            # New: channels().list() = 1 + playlistItems().list() = 1 + videos().list() = 1 = 3 total
            # This gives us ~33x more checks per day with the same quota!
            #
            # LIMITATION: Only detects streams if they are the MOST RECENT upload on the channel.
            # If the channel uploads other content (VODs, Shorts, premieres) after going live,
            # the stream won't be detected. This is fine for most streamers who don't upload
            # during their streams, but may affect 24/7 channels or high-activity uploaders.
            #
            # For 100% reliable detection (at cost of 101 units/check), use search().list(eventType=live)
            # See docs/platforms/streaming/youtube.md for details and alternative implementation.
            
            # Step 1: Get channel's uploads playlist (1 unit)
            # This checks the channel's current live broadcast
            request = self.client.channels().list(
                part="contentDetails",
                id=channel_id_to_check
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.debug(f"No YouTube channel found for ID: {channel_id_to_check}")
                return False, None
            
            # Step 2: Get the most recent video from uploads playlist (1 unit)
            # If they're live, their livestream will be the most recent upload
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get the most recent upload (1 unit)
            playlist_request = self.client.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=1
            )
            playlist_response = playlist_request.execute()
            
            if not playlist_response.get('items'):
                logger.debug(f"No uploads found for YouTube channel")
                return False, None
            
            video_id = playlist_response['items'][0]['snippet']['resourceId']['videoId']
            
            # Step 3: Check if this video is currently live (1 unit)
            video_request = self.client.videos().list(
                part="liveStreamingDetails,snippet",
                id=video_id
            )
            video_response = video_request.execute()
            
            if video_response.get('items'):
                video_data = video_response['items'][0]
                
                # Check if actually live (has liveStreamingDetails and no actualEndTime)
                live_details = video_data.get('liveStreamingDetails')
                if not live_details or live_details.get('actualEndTime'):
                    return False, None
                
                # Safe field access with defaults
                snippet = video_data.get('snippet', {})
                title = snippet.get('title', 'Untitled Stream')
                thumbnails = snippet.get('thumbnails', {})
                thumbnail_url = thumbnails.get('high', {}).get('url') or thumbnails.get('medium', {}).get('url')
                
                # Get concurrent viewers if available
                viewer_count = live_details.get('concurrentViewers')
                if viewer_count:
                    try:
                        viewer_count = int(viewer_count)
                    except (ValueError, TypeError):
                        viewer_count = None
                
                stream_data = {
                    'title': title,
                    'viewer_count': viewer_count,
                    'thumbnail_url': thumbnail_url,
                    'game_name': None  # YouTube doesn't have game/category in API
                }
                
                # Reset error counter on success
                self.consecutive_errors = 0
                return True, stream_data
                
            return False, None
            
        except Exception as e:
            # Check if it's a quota exceeded error
            self.consecutive_errors += 1
            error_str = str(e)
            if 'quotaExceeded' in error_str or 'quota' in error_str.lower():
                if not self.quota_exceeded:
                    # First time hitting quota limit
                    from datetime import datetime
                    self.quota_exceeded = True
                    self.quota_exceeded_time = datetime.now()
                    logger.error(f"❌ YouTube API quota exceeded! Pausing YouTube checks for 1 hour.")
                    logger.error(f"   YouTube has strict daily quotas. Consider:")
                    logger.error(f"   • Increasing check interval (SETTINGS_CHECK_INTERVAL)")
                    logger.error(f"   • Disabling YouTube monitoring temporarily")
                    logger.error(f"   • Requesting quota increase from Google Cloud Console")
                else:
                    logger.debug(f"YouTube quota still exceeded (cooldown active)")
            else:
                logger.error(f"⚠ Error checking YouTube: {e} (consecutive errors: {self.consecutive_errors})")
            return False, None
    
    def _resolve_channel_id(self, username):
        """Resolve a channel ID from a username/handle (for any user, not just authenticated one)."""
        try:
            # Ensure username has @ prefix for handle-based lookup
            lookup_username = username if username.startswith('@') else f'@{username}'
            
            # Try modern handle format first (@username)
            request = self.client.channels().list(
                part="id",
                forHandle=lookup_username
            )
            
            response = request.execute()
            if response.get('items'):
                channel_id = response['items'][0]['id']
                logger.debug(f"✓ Resolved YouTube channel ID for {username}: {channel_id}")
                return channel_id
            
            # If handle didn't work and original didn't have @, try legacy username
            if not username.startswith('@'):
                request = self.client.channels().list(
                    part="id",
                    forUsername=username
                )
                response = request.execute()
                if response.get('items'):
                    channel_id = response['items'][0]['id']
                    logger.debug(f"✓ Resolved YouTube channel ID for {username}: {channel_id}")
                    return channel_id
            
            return None
        except Exception as e:
            logger.warning(f"Error resolving YouTube channel ID for {username}: {e}")
            return None


class KickPlatform(StreamingPlatform):
    """Kick streaming platform with optional authentication."""
    
    def __init__(self):
        super().__init__("Kick")
        self.enabled = False
        self.access_token = None
        self.use_auth = False
        
    def authenticate(self):
        """Authenticate with Kick API (optional - falls back to public API)."""
        if not get_bool_config('Kick', 'enable', default=False):
            return False
        
        # Try to get credentials for authenticated API
        client_id = get_secret('Kick', 'client_id',
                              secret_name_env='SECRETS_AWS_KICK_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_KICK_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
        client_secret = get_secret('Kick', 'client_secret',
                                   secret_name_env='SECRETS_AWS_KICK_SECRET_NAME',
                                   secret_path_env='SECRETS_VAULT_KICK_SECRET_PATH',
                                   doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
        
        if client_id and client_secret:
            # Try to get access token using OAuth client credentials flow
            try:
                # Use correct OAuth server endpoint (id.kick.com, not api.kick.com)
                token_url = "https://id.kick.com/oauth/token"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                response = requests.post(token_url, data=data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get('access_token')
                    self.use_auth = True
                    self.enabled = True
                    logger.info("✓ Kick authenticated (using official API)")
                    return True
                else:
                    logger.warning(f"⚠ Kick authentication failed (status {response.status_code}), falling back to public API")
            except Exception as e:
                logger.warning(f"⚠ Kick authentication error: {e}, falling back to public API")
        
        # Fall back to public API
        self.enabled = True
        self.use_auth = False
        logger.info("✓ Kick enabled (using public API)")
        return True
    
    def is_live(self, username):
        if not self.enabled:
            return False, None
        
        try:
            if self.use_auth and self.access_token:
                # Use official authenticated API
                return self._check_authenticated(username)
            else:
                # Fall back to public scraping API
                return self._check_public(username)
        except Exception as e:
            logger.error(f"Error checking Kick: {e}")
            return False, None
    
    def _check_authenticated(self, username):
        """Check stream status using authenticated official Kick API."""
        try:
            # Use the /channels endpoint with slug parameter (works better than searching livestreams)
            channels_url = "https://api.kick.com/public/v1/channels"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            params = {'slug': username}
            response = requests.get(channels_url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Kick channels API failed: {response.status_code}, falling back to public API")
                return self._check_public(username)
            
            result = response.json()
            channels = result.get('data', [])
            
            if not channels:
                # Channel not found or offline
                return False, None
            
            channel = channels[0]
            
            # Check if livestream is active
            stream = channel.get('stream', {})
            is_live = stream.get('is_live', False)
            
            if not is_live:
                return False, None
            
            # Extract stream information
            stream_title = channel.get('stream_title', 'Live Stream')
            viewer_count = stream.get('viewer_count')
            thumbnail_url = stream.get('thumbnail')
            
            category = channel.get('category', {})
            game_name = category.get('name') if isinstance(category, dict) else None
            
            stream_data = {
                'title': stream_title,
                'viewer_count': int(viewer_count) if viewer_count is not None else None,
                'thumbnail_url': thumbnail_url,
                'game_name': game_name
            }
            
            return True, stream_data

            
        except Exception as e:
            logger.warning(f"Authenticated Kick check failed: {e}, trying public API")
            return self._check_public(username)
    
    def _check_public(self, username):
        """Check stream status using public API (fallback)."""
        try:
            # Old public API endpoint
            url = f"https://kick.com/api/v2/channels/{username}/livestream"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://kick.com/'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and data.get('data'):
                    livestream = data['data']
                    if livestream.get('is_live'):
                        title = livestream.get('session_title', 'Live Stream')
                        viewer_count = livestream.get('viewer_count') or livestream.get('viewers')
                        thumbnail_url = livestream.get('thumbnail', {}).get('url') if livestream.get('thumbnail') else None
                        category = livestream.get('category', {})
                        game_name = category.get('name') if category else None
                        
                        stream_data = {
                            'title': title,
                            'viewer_count': int(viewer_count) if viewer_count else None,
                            'thumbnail_url': thumbnail_url,
                            'game_name': game_name
                        }
                        return True, stream_data
            
            return False, None
            
        except Exception as e:
            raise  # Re-raise to be caught by parent


# ===========================================
# MESSAGE GENERATION HELPERS
# ===========================================

def get_message_for_stream(ai_generator: AIMessageGenerator,
                           is_stream_start: bool,
                           platform_name: str,
                           username: str,
                           title: str,
                           url: str,
                           social_platform_name: str,
                           fallback_messages: list) -> str:
    """
    Get message for stream announcement, using AI if enabled, otherwise fallback.
    
    Args:
        ai_generator: AI message generator instance
        is_stream_start: True for start, False for end
        platform_name: Streaming platform (Twitch, YouTube, Kick)
        username: Streamer username
        title: Stream title
        url: Stream URL (for start messages)
        social_platform_name: Social platform name (bluesky, mastodon, discord, matrix)
        fallback_messages: List of template messages to use if AI disabled
    
    Returns:
        Formatted message ready to post
    """
    # Try AI generation if enabled
    if ai_generator.enabled:
        try:
            if is_stream_start:
                ai_message = ai_generator.generate_stream_start_message(
                    platform_name=platform_name,
                    username=username,
                    title=title,
                    url=url,
                    social_platform=social_platform_name
                )
                if ai_message:
                    return ai_message
                logger.warning("⚠ AI generation returned None, using fallback message")
            else:
                ai_message = ai_generator.generate_stream_end_message(
                    platform_name=platform_name,
                    username=username,
                    title=title,
                    social_platform=social_platform_name
                )
                if ai_message:
                    return ai_message
                logger.warning("⚠ AI generation returned None, using fallback message")
        except Exception as e:
            logger.error(f"✗ AI message generation failed: {e}, using fallback")
    
    # Fallback to traditional messages
    if not fallback_messages:
        logger.error(f"✗ No fallback messages available for {platform_name}")
        return f"🎮 {username} is {'now live' if is_stream_start else 'done streaming'} on {platform_name}! {title}"
    
    # Pick random fallback and format it
    message = random.choice(fallback_messages).format(
        stream_title=title,
        username=username,
        platform=platform_name
    )
    return message


def post_to_social_async(enabled_social: list,
                         ai_generator: AIMessageGenerator,
                         is_stream_start: bool,
                         platform_name: str,
                         username: str,
                         title: str,
                         url: str,
                         fallback_messages: list,
                         stream_data: Optional[dict] = None,
                         reply_to_ids: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
    """
    Post to all social platforms asynchronously using ThreadPoolExecutor.
    
    Args:
        enabled_social: List of enabled social platform instances
        ai_generator: AI message generator
        is_stream_start: True for stream start, False for end
        platform_name: Streaming platform name
        username: Streamer username
        title: Stream title
        url: Stream URL
        fallback_messages: Fallback messages if AI fails
        stream_data: Optional stream metadata for embeds
        reply_to_ids: Optional dict of {social_name: post_id} for threading
        
    Returns:
        Dict mapping social platform names to post IDs (or None if failed)
    """
    def post_to_single_platform(social):
        """Helper function to post to a single platform."""
        try:
            # Generate message with AI or fallback
            message = get_message_for_stream(
                ai_generator=ai_generator,
                is_stream_start=is_stream_start,
                platform_name=platform_name,
                username=username,
                title=title,
                url=url,
                social_platform_name=social.name.lower(),
                fallback_messages=fallback_messages
            )
            
            # Get reply_to_id if threading
            reply_to_id = None
            if reply_to_ids:
                reply_to_id = reply_to_ids.get(social.name)
            
            # Post to platform
            post_id = social.post(
                message,
                reply_to_id=reply_to_id,
                platform_name=platform_name,
                stream_data=stream_data
            )
            
            if post_id:
                logger.debug(f"  ✓ Posted to {social.name} (ID: {post_id})")
            else:
                logger.debug(f"  ✗ Failed to post to {social.name}")
                
            return (social.name, post_id)
        except Exception as e:
            logger.error(f"✗ Error posting to {social.name}: {e}")
            return (social.name, None)
    
    # Post to all platforms in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=len(enabled_social)) as executor:
        futures = [executor.submit(post_to_single_platform, social) for social in enabled_social]
        for future in as_completed(futures):
            social_name, post_id = future.result()
            results[social_name] = post_id
    
    return results


# ===========================================
# MAIN APPLICATION
# ===========================================

def main():
    """Main application loop with improved state tracking and per-platform posting."""
    
    logger.info("="*60)
    logger.info("🚀 Stream Daemon Starting...")
    logger.info("="*60)
    
    # Initialize streaming platforms
    streaming_platforms = [
        TwitchPlatform(),
        YouTubePlatform(),
        KickPlatform()
    ]
    
    enabled_streaming = []
    for platform in streaming_platforms:
        if platform.authenticate():
            enabled_streaming.append(platform)
    
    if not enabled_streaming:
        logger.error("✗ No streaming platforms configured!")
        logger.error("   Enable at least one: Twitch, YouTube, or Kick")
        sys.exit(1)
    
    # Initialize social platforms
    social_platforms = [
        MastodonPlatform(),
        BlueskyPlatform(),
        DiscordPlatform(),
        MatrixPlatform()
    ]
    
    enabled_social = []
    for platform in social_platforms:
        if platform.authenticate():
            enabled_social.append(platform)
    
    if not enabled_social:
        logger.error("✗ No social platforms configured!")
        logger.error("   Enable at least one: Mastodon, Bluesky, Discord, or Matrix")
        sys.exit(1)
    
    # Initialize AI message generator (optional)
    ai_generator = AIMessageGenerator()
    ai_generator.authenticate()  # Will log if enabled/disabled
    
    # Load messages from consolidated files with platform sections
    messages_file = get_config('Messages', 'messages_file', default='messages.txt')
    end_messages_file = get_config('Messages', 'end_messages_file', default='end_messages.txt')
    
    # Load new threading mode configurations
    live_threading_mode = get_config('Messages', 'live_threading_mode', default='separate').lower()
    end_threading_mode = get_config('Messages', 'end_threading_mode', default='thread').lower()
    
    # Backwards compatibility with old config
    post_end_stream_message = get_bool_config('Messages', 'post_end_stream_message', default=True)
    if not post_end_stream_message:
        end_threading_mode = 'disabled'
    
    # Validate threading modes
    valid_live_modes = ['separate', 'thread', 'combined']
    valid_end_modes = ['disabled', 'separate', 'thread', 'combined', 'single_when_all_end']
    
    if live_threading_mode not in valid_live_modes:
        logger.warning(f"⚠ Invalid LIVE_THREADING_MODE '{live_threading_mode}', using 'separate'")
        live_threading_mode = 'separate'
    
    if end_threading_mode not in valid_end_modes:
        logger.warning(f"⚠ Invalid END_THREADING_MODE '{end_threading_mode}', using 'thread'")
        end_threading_mode = 'thread'
    
    logger.info(f"📋 Live posting mode: {live_threading_mode}")
    logger.info(f"📋 End posting mode: {end_threading_mode}")
    
    use_platform_specific = get_bool_config('Messages', 'use_platform_specific_messages', default=True)
    
    # Parse message files
    logger.info(f"📝 Loading messages from {messages_file} and {end_messages_file}")
    live_sections = parse_sectioned_message_file(messages_file)
    end_sections = parse_sectioned_message_file(end_messages_file)
    
    if not live_sections:
        logger.error(f"✗ Failed to load messages from {messages_file}")
        sys.exit(1)
    
    # Check if we have DEFAULT section
    has_default = 'DEFAULT' in live_sections
    has_end_default = 'DEFAULT' in end_sections
    
    # Build messages dict for each platform
    messages = {}  # platform_name -> list of messages
    end_messages = {}  # platform_name -> list of end messages
    
    for platform in enabled_streaming:
        platform_name = platform.name.upper()
        
        # Live messages
        if use_platform_specific and platform_name in live_sections:
            messages[platform.name] = live_sections[platform_name]
            logger.info(f"  • Loaded {len(messages[platform.name])} platform-specific live messages for {platform.name}")
        elif has_default:
            messages[platform.name] = live_sections['DEFAULT']
            logger.info(f"  • Using {len(messages[platform.name])} DEFAULT live messages for {platform.name}")
        else:
            logger.error(f"✗ No messages found for {platform.name} (no platform section and no DEFAULT)")
            sys.exit(1)
        
        # End messages (optional)
        if use_platform_specific and platform_name in end_sections:
            end_messages[platform.name] = end_sections[platform_name]
            logger.info(f"  • Loaded {len(end_messages[platform.name])} platform-specific end messages for {platform.name}")
        elif has_end_default:
            end_messages[platform.name] = end_sections['DEFAULT']
            logger.info(f"  • Using {len(end_messages[platform.name])} DEFAULT end messages for {platform.name}")
        else:
            end_messages[platform.name] = []
            logger.debug(f"  • No end messages for {platform.name} (optional)")
    
    # Get usernames for each platform and create StreamStatus trackers
    stream_statuses: Dict[str, StreamStatus] = {}
    for platform in enabled_streaming:
        username = get_config(platform.name, 'username')
        if username:
            status = StreamStatus(
                platform_name=platform.name,
                username=username
            )
            stream_statuses[platform.name] = status
            logger.info(f"  • Monitoring {platform.name}/{username}")
        else:
            logger.warning(f"⚠ No username configured for {platform.name}, skipping")
    
    if not stream_statuses:
        logger.error("✗ No usernames configured for any streaming platforms!")
        sys.exit(1)
    
    # Settings
    post_interval = get_int_config('Settings', 'post_interval', default=1)
    check_interval = get_int_config('Settings', 'check_interval', default=5)
    
    # Track platforms that went live in this session (for single_when_all_end mode)
    platforms_that_went_live = set()
    last_live_post_ids = {}  # For combined/thread modes: social_platform -> last_post_id
    
    logger.info("="*60)
    logger.info(f"📺 Monitoring: {', '.join([f'{s.platform_name}/{s.username}' for s in stream_statuses.values()])}")
    logger.info(f"📱 Posting to: {', '.join([p.name for p in enabled_social])}")
    logger.info(f"⏰ Check: {check_interval}min (offline) / {post_interval}min (live)")
    logger.info("="*60)
    
    # Main loop with improved state tracking
    while True:
        try:
            logger.info("🔍 Checking streams...")
            
            # Collect platforms that just went live or offline in this check cycle
            platforms_went_live = []
            platforms_went_offline = []
            
            # Check all streaming platforms
            for platform in enabled_streaming:
                status = stream_statuses.get(platform.name)
                if not status:
                    continue
                
                # Check if stream is live (returns is_live bool and stream_data dict)
                is_live, stream_data = platform.is_live(status.username)
                
                # Update status and check if state changed
                state_changed = status.update(is_live, stream_data)
                
                if state_changed:
                    if status.state == StreamState.LIVE:
                        platforms_went_live.append(status)
                        platforms_that_went_live.add(status.platform_name)
                    elif status.state == StreamState.OFFLINE:
                        platforms_went_offline.append(status)
                else:
                    # No state change - just log current status
                    if status.state == StreamState.LIVE:
                        logger.debug(f"  {status.platform_name}/{status.username}: Still live ({status.consecutive_live_checks} checks)")
                        
                        # Update Discord embeds with fresh stream data (viewer count, thumbnail)
                        for social in enabled_social:
                            if isinstance(social, DiscordPlatform) and status.stream_data:
                                if social.update_stream(status.platform_name, status.stream_data, status.url):
                                    logger.info(f"  ✓ Updated Discord embed for {status.platform_name} (viewers: {status.stream_data.get('viewer_count', 'N/A')})")
                    else:
                        logger.debug(f"  {status.platform_name}/{status.username}: Still offline ({status.consecutive_offline_checks} checks)")
            
            # ================================================================
            # HANDLE PLATFORMS THAT WENT LIVE
            # ================================================================
            if platforms_went_live:
                if live_threading_mode == 'combined':
                    # COMBINED MODE: Single post listing all platforms
                    platform_names = ', '.join([s.platform_name for s in platforms_went_live])
                    titles = ' | '.join([f"{s.platform_name}: {s.title}" for s in platforms_went_live])
                    
                    # Use first platform's info for URL generation
                    first_platform = platforms_went_live[0]
                    platform_messages = messages.get(first_platform.platform_name, [])
                    
                    logger.info(f"📢 Posting combined 'LIVE' announcement for {platform_names}")
                    
                    # Post to all platforms asynchronously
                    post_results = post_to_social_async(
                        enabled_social=enabled_social,
                        ai_generator=ai_generator,
                        is_stream_start=True,
                        platform_name=platform_names,
                        username=first_platform.username,
                        title=titles,
                        url=first_platform.url or '',
                        fallback_messages=platform_messages,
                        stream_data=first_platform.stream_data,
                        reply_to_ids=None
                    )
                    
                    # Process results
                    posted_count = 0
                    for social_name, post_id in post_results.items():
                        if post_id:
                            posted_count += 1
                            last_live_post_ids[social_name] = post_id
                            # Save post ID to each platform status for potential end threading
                            for status in platforms_went_live:
                                status.last_post_ids[social_name] = post_id
                    
                    if posted_count > 0:
                        logger.info(f"✓ Posted to {posted_count}/{len(enabled_social)} platform(s)")
                    else:
                        logger.warning(f"⚠ Failed to post to any platforms")
                
                else:
                    # SEPARATE or THREAD MODE: Post for each platform
                    for idx, status in enumerate(platforms_went_live):
                        platform_messages = messages.get(status.platform_name, [])
                        if not platform_messages:
                            logger.error(f"✗ No messages configured for {status.platform_name}")
                            continue
                        
                        logger.info(f"📢 Posting 'LIVE' announcement for {status.platform_name}/{status.username}")
                        
                        # Determine reply_to_ids for threading
                        reply_to_ids = None
                        if live_threading_mode == 'thread' and idx > 0:
                            # Thread to previous posts
                            reply_to_ids = last_live_post_ids.copy()
                        
                        # Post to all platforms asynchronously
                        post_results = post_to_social_async(
                            enabled_social=enabled_social,
                            ai_generator=ai_generator,
                            is_stream_start=True,
                            platform_name=status.platform_name,
                            username=status.username,
                            title=status.title,
                            url=status.url or '',
                            fallback_messages=platform_messages,
                            stream_data=status.stream_data,
                            reply_to_ids=reply_to_ids
                        )
                        
                        # Process results
                        posted_count = 0
                        for social_name, post_id in post_results.items():
                            if post_id:
                                posted_count += 1
                                last_live_post_ids[social_name] = post_id
                                status.last_post_ids[social_name] = post_id
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted to {posted_count}/{len(enabled_social)} platform(s)")
                        else:
                            logger.warning(f"⚠ Failed to post to any platforms")
            
            # ================================================================
            # HANDLE PLATFORMS THAT WENT OFFLINE
            # ================================================================
            if platforms_went_offline and end_threading_mode != 'disabled':
                
                if end_threading_mode == 'single_when_all_end':
                    # Check if ALL platforms that went live are now offline
                    all_ended = all(
                        stream_statuses[pname].state == StreamState.OFFLINE 
                        for pname in platforms_that_went_live
                    )
                    
                    if all_ended and platforms_that_went_live:
                        # Post single "all streams ended" message
                        platform_names = ', '.join(sorted(platforms_that_went_live))
                        
                        # Use first platform's end messages as template
                        first_platform_name = next(iter(platforms_that_went_live))
                        first_status = stream_statuses[first_platform_name]
                        platform_end_messages = end_messages.get(first_platform_name, [])
                        
                        if platform_end_messages:
                            logger.info(f"📢 Posting final 'ALL STREAMS ENDED' announcement for {platform_names}")
                            
                            # Handle Discord separately (update embeds)
                            discord_count = 0
                            for social in enabled_social:
                                if isinstance(social, DiscordPlatform):
                                    for pname in platforms_that_went_live:
                                        status = stream_statuses[pname]
                                        if social.end_stream(status.platform_name, status.stream_data or {}, status.url):
                                            discord_count += 1
                                            logger.debug(f"  ✓ Updated Discord embed for {status.platform_name}")
                            
                            # Post to non-Discord platforms asynchronously
                            non_discord_social = [s for s in enabled_social if not isinstance(s, DiscordPlatform)]
                            if non_discord_social:
                                post_results = post_to_social_async(
                                    enabled_social=non_discord_social,
                                    ai_generator=ai_generator,
                                    is_stream_start=False,
                                    platform_name=platform_names,
                                    username=first_status.username,
                                    title=first_status.title,
                                    url='',
                                    fallback_messages=platform_end_messages,
                                    stream_data=None,
                                    reply_to_ids=last_live_post_ids.copy()
                                )
                                
                                posted_count = discord_count + sum(1 for pid in post_results.values() if pid)
                            else:
                                posted_count = discord_count
                            
                            if posted_count > 0:
                                logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
                            
                            # Clear tracking since all streams ended
                            platforms_that_went_live.clear()
                            last_live_post_ids.clear()
                    else:
                        logger.debug(f"  Waiting for all streams to end (mode: single_when_all_end)")
                
                elif end_threading_mode == 'combined':
                    # COMBINED MODE: Single post for all platforms that ended
                    platform_names = ', '.join([s.platform_name for s in platforms_went_offline])
                    
                    # Use first platform's end messages
                    first_status = platforms_went_offline[0]
                    platform_end_messages = end_messages.get(first_status.platform_name, [])
                    
                    if platform_end_messages:
                        logger.info(f"📢 Posting combined 'OFFLINE' announcement for {platform_names}")
                        
                        # Handle Discord separately (update embeds)
                        discord_count = 0
                        for social in enabled_social:
                            if isinstance(social, DiscordPlatform):
                                for status in platforms_went_offline:
                                    if social.end_stream(status.platform_name, status.stream_data or {}, status.url):
                                        discord_count += 1
                                        logger.debug(f"  ✓ Updated Discord embed for {status.platform_name}")
                        
                        # Post to non-Discord platforms asynchronously
                        non_discord_social = [s for s in enabled_social if not isinstance(s, DiscordPlatform)]
                        if non_discord_social:
                            post_results = post_to_social_async(
                                enabled_social=non_discord_social,
                                ai_generator=ai_generator,
                                is_stream_start=False,
                                platform_name=platform_names,
                                username=first_status.username,
                                title=first_status.title,
                                url='',
                                fallback_messages=platform_end_messages,
                                stream_data=None,
                                reply_to_ids=last_live_post_ids.copy()
                            )
                            
                            posted_count = discord_count + sum(1 for pid in post_results.values() if pid)
                        else:
                            posted_count = discord_count
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
                
                else:
                    # SEPARATE or THREAD MODE: Post for each platform
                    for status in platforms_went_offline:
                        platform_end_messages = end_messages.get(status.platform_name, [])
                        if not platform_end_messages:
                            logger.debug(f"  No end messages for {status.platform_name}")
                            continue
                        
                        logger.info(f"📢 Posting 'OFFLINE' announcement for {status.platform_name}/{status.username}")
                        
                        # Handle Discord separately (update embed)
                        discord_count = 0
                        for social in enabled_social:
                            if isinstance(social, DiscordPlatform):
                                if social.end_stream(status.platform_name, status.stream_data or {}, status.url):
                                    discord_count += 1
                                    logger.debug(f"  ✓ Updated Discord embed to show stream ended")
                        
                        # Determine reply_to_ids for threading
                        reply_to_ids = None
                        if end_threading_mode == 'thread':
                            # Thread to this platform's live announcement
                            reply_to_ids = status.last_post_ids.copy()
                        
                        # Post to non-Discord platforms asynchronously
                        non_discord_social = [s for s in enabled_social if not isinstance(s, DiscordPlatform)]
                        if non_discord_social:
                            post_results = post_to_social_async(
                                enabled_social=non_discord_social,
                                ai_generator=ai_generator,
                                is_stream_start=False,
                                platform_name=status.platform_name,
                                username=status.username,
                                title=status.title,
                                url='',
                                fallback_messages=platform_end_messages,
                                stream_data=None,
                                reply_to_ids=reply_to_ids
                            )
                            
                            posted_count = discord_count + sum(1 for pid in post_results.values() if pid)
                        else:
                            posted_count = discord_count
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
            
            # Determine sleep time based on any active streams
            any_live = any(s.state == StreamState.LIVE for s in stream_statuses.values())
            if any_live:
                sleep_time = post_interval * 60  # POST_INTERVAL is now in minutes, not hours
                live_platforms = [s.platform_name for s in stream_statuses.values() if s.state == StreamState.LIVE]
                logger.info(f"⏰ Streams active ({', '.join(live_platforms)}), checking again in {post_interval} minute(s)")
            else:
                sleep_time = check_interval * 60
                logger.info(f"⏰ No streams live, checking again in {check_interval} minute(s)")
            
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Stream Daemon stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info(f"Retrying in {check_interval} minute(s)...")
            time.sleep(check_interval * 60)


if __name__ == "__main__":
    main()
