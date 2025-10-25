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


    
    def is_live(self, username):
        """Check if user is live. Returns (is_live, stream_title) tuple."""
        raise NotImplementedError
    
    def authenticate(self):
        """Authenticate with the platform."""
        raise NotImplementedError


class TwitchPlatform(StreamingPlatform):
    """Twitch streaming platform."""
    
    def __init__(self):
        super().__init__("Twitch")
        self.client = None
        self.client_id = None
        self.client_secret = None
        
    def authenticate(self):
        self.client_id = get_secret('Twitch', 'client_id', 
                              secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
        self.client_secret = get_secret('Twitch', 'client_secret',
                                   secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
                                   secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH',
                                   doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
        
        if not all([self.client_id, self.client_secret]):
            return False
            
        try:
            # Test authentication by creating a client
            async def test_auth():
                client = await Twitch(self.client_id, self.client_secret)
                await client.close()
                return True
            
            asyncio.run(test_auth())
            self.enabled = True
            logger.info("✓ Twitch authenticated")
            return True
        except Exception as e:
            logger.warning(f"✗ Twitch authentication failed: {e}")
            return False
    
    def is_live(self, username):
        if not self.enabled or not self.client_id:
            return False, None
            
        try:
            # Run async check synchronously
            async def check_live():
                client = None
                try:
                    client = await Twitch(self.client_id, self.client_secret)
                    
                    # Get user info
                    user_generator = client.get_users(logins=[username])
                    users = []
                    async for user in user_generator:
                        users.append(user)
                    
                    if not users:
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
                        # Return tuple: (is_live, title, viewer_count, thumbnail_url, game_name)
                        stream_data = {
                            'title': stream.title,
                            'viewer_count': stream.viewer_count,
                            'thumbnail_url': stream.thumbnail_url.replace('{width}', '1280').replace('{height}', '720') if stream.thumbnail_url else None,
                            'game_name': stream.game_name
                        }
                        return True, stream_data
                    return False, None
                finally:
                    if client:
                        await client.close()
            
            return asyncio.run(check_live())
        except Exception as e:
            logger.error(f"Error checking Twitch: {e}")
            return False, None


class YouTubePlatform(StreamingPlatform):
    """YouTube Live streaming platform."""
    
    def __init__(self):
        super().__init__("YouTube")
        self.client = None
        self.channel_id = None
        self.username = None
        self.quota_exceeded = False
        self.quota_exceeded_time = None
        
    def authenticate(self):
        api_key = get_secret('YouTube', 'api_key',
                            secret_name_env='SECRETS_AWS_YOUTUBE_SECRET_NAME',
                            secret_path_env='SECRETS_VAULT_YOUTUBE_SECRET_PATH',
                            doppler_secret_env='SECRETS_DOPPLER_YOUTUBE_SECRET_NAME')
        self.username = get_config('YouTube', 'username')
        
        # Optional: Channel ID for direct lookup (faster, but username works too)
        self.channel_id = get_config('YouTube', 'channel_id')
        
        if not api_key or not self.username:
            return False
            
        try:
            self.client = build('youtube', 'v3', developerKey=api_key)
            
            # If channel_id not provided, look it up by username/handle
            if not self.channel_id:
                self.channel_id = self._get_channel_id_from_username()
                if not self.channel_id:
                    logger.warning(f"✗ Could not find YouTube channel for username: {self.username}")
                    return False
            
            self.enabled = True
            logger.info("✓ YouTube authenticated")
            return True
        except Exception as e:
            logger.warning(f"✗ YouTube authentication failed: {e}")
            return False
    
    def _get_channel_id_from_username(self):
        """Convert username/handle to channel ID."""
        try:
            # Ensure username has @ prefix for handle-based lookup
            lookup_username = self.username if self.username.startswith('@') else f'@{self.username}'
            
            # Try modern handle format first (@username)
            request = self.client.channels().list(
                part="id",
                forHandle=lookup_username
            )
            
            response = request.execute()
            if response.get('items'):
                channel_id = response['items'][0]['id']
                logger.info(f"✓ Resolved YouTube channel ID: {channel_id}")
                return channel_id
            
            # If handle didn't work and original didn't have @, try legacy username
            if not self.username.startswith('@'):
                request = self.client.channels().list(
                    part="id",
                    forUsername=self.username
                )
                response = request.execute()
                if response.get('items'):
                    channel_id = response['items'][0]['id']
                    logger.info(f"✓ Resolved YouTube channel ID: {channel_id}")
                    return channel_id
            
            return None
        except Exception as e:
            logger.warning(f"Error resolving YouTube channel ID: {e}")
            return None
    
    def is_live(self, username=None):
        """Check if a YouTube channel is live.
        
        Args:
            username: Optional username/handle to check. If not provided, uses self.username.
                     Can be in format '@handle' or 'channelname'
        """
        if not self.enabled or not self.client:
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
        
        # Determine which channel to check
        channel_id_to_check = None
        
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
            return False, None
            
        try:
            # OPTIMIZED API USAGE (3 units total vs 101 units before!)
            # Old: search().list(eventType=live) = 100 units + videos().list() = 1 unit = 101 total
            # New: channels().list() = 1 + playlistItems().list() = 1 + videos().list() = 1 = 3 total
            # This gives us ~33x more checks per day with the same quota!
            
            # Step 1: Get channel's uploads playlist (1 unit)
            # This checks the channel's current live broadcast
            request = self.client.channels().list(
                part="contentDetails",
                id=channel_id_to_check
            )
            response = request.execute()
            
            if not response.get('items'):
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
                
                title = video_data['snippet']['title']
                thumbnail_url = video_data['snippet']['thumbnails'].get('high', {}).get('url')
                
                # Get concurrent viewers if available
                viewer_count = live_details.get('concurrentViewers')
                if viewer_count:
                    viewer_count = int(viewer_count)
                
                stream_data = {
                    'title': title,
                    'viewer_count': viewer_count,
                    'thumbnail_url': thumbnail_url,
                    'game_name': None  # YouTube doesn't have game/category in API
                }
                return True, stream_data
                
            return False, None
        except Exception as e:
            # Check if it's a quota exceeded error
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
                logger.error(f"Error checking YouTube: {e}")
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
# SOCIAL PLATFORM CLASSES
# ===========================================

class SocialPlatform:
    """Base class for social platforms."""
    
    def __init__(self, name):
        self.name = name
        self.enabled = False
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None) -> Optional[str]:
        """
        Post message to platform.
        
        Args:
            message: The message to post
            reply_to_id: Optional post ID to reply to (for threading)
            platform_name: Optional streaming platform name (for role mentions in Discord/Matrix)
            
        Returns:
            Post ID if successful, None otherwise
        """
        raise NotImplementedError
    
    def authenticate(self):
        """Authenticate with the platform."""
        raise NotImplementedError


class MastodonPlatform(SocialPlatform):
    """Mastodon social platform with threading support."""
    
    def __init__(self):
        super().__init__("Mastodon")
        self.client = None
        
    def authenticate(self):
        if not get_bool_config('Mastodon', 'enable_posting', default=False):
            return False
            
        client_id = get_secret('Mastodon', 'client_id',
                              secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
        client_secret = get_secret('Mastodon', 'client_secret',
                                   secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                                   secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                                   doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
        access_token = get_secret('Mastodon', 'access_token',
                                  secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                                  secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                                  doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
        api_base_url = get_config('Mastodon', 'api_base_url')
        
        if not all([client_id, client_secret, access_token, api_base_url]):
            return False
            
        try:
            self.client = Mastodon(
                client_id=client_id,
                client_secret=client_secret,
                access_token=access_token,
                api_base_url=api_base_url
            )
            self.enabled = True
            logger.info("✓ Mastodon authenticated")
            return True
        except Exception as e:
            logger.warning(f"✗ Mastodon authentication failed: {e}")
            return False
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
            
        try:
            # Check if we should attach a thumbnail image
            media_ids = []
            if stream_data:
                thumbnail_url = stream_data.get('thumbnail_url')
                if thumbnail_url:
                    try:
                        import requests
                        import tempfile
                        import os
                        
                        # Download thumbnail
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                        }
                        img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                        
                        if img_response.status_code == 200:
                            # Determine file extension from content type or URL
                            content_type = img_response.headers.get('content-type', '')
                            if 'jpeg' in content_type or 'jpg' in content_type or thumbnail_url.endswith('.jpg'):
                                ext = '.jpg'
                            elif 'png' in content_type or thumbnail_url.endswith('.png'):
                                ext = '.png'
                            elif 'webp' in content_type or thumbnail_url.endswith('.webp'):
                                ext = '.webp'
                            else:
                                ext = '.jpg'  # Default fallback
                            
                            # Save to temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                                tmp_file.write(img_response.content)
                                tmp_path = tmp_file.name
                            
                            try:
                                # Upload to Mastodon
                                # Build description with stream info
                                viewer_count = stream_data.get('viewer_count', 0)
                                game_name = stream_data.get('game_name', '')
                                description = f"🔴 LIVE"
                                if viewer_count:
                                    description += f" • {viewer_count:,} viewers"
                                if game_name:
                                    description += f" • {game_name}"
                                
                                media = self.client.media_post(tmp_path, description=description)
                                media_ids.append(media['id'])
                                logger.info(f"✓ Uploaded thumbnail to Mastodon (media ID: {media['id']})")
                            finally:
                                # Clean up temp file
                                os.unlink(tmp_path)
                    except Exception as img_error:
                        logger.warning(f"⚠ Could not upload thumbnail to Mastodon: {img_error}")
            
            # Post as a reply if reply_to_id is provided (threading)
            status = self.client.status_post(
                message, 
                in_reply_to_id=reply_to_id,
                media_ids=media_ids if media_ids else None
            )
            return str(status['id'])
        except Exception as e:
            logger.error(f"✗ Mastodon post failed: {e}")
            return None


class BlueskyPlatform(SocialPlatform):
    """Bluesky social platform with threading support."""
    
    def __init__(self):
        super().__init__("Bluesky")
        self.client = None
        
    def authenticate(self):
        if not get_bool_config('Bluesky', 'enable_posting', default=False):
            return False
            
        handle = get_config('Bluesky', 'handle')
        app_password = get_secret('Bluesky', 'app_password',
                                  secret_name_env='SECRETS_AWS_BLUESKY_SECRET_NAME',
                                  secret_path_env='SECRETS_VAULT_BLUESKY_SECRET_PATH',
                                  doppler_secret_env='SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
        
        if not all([handle, app_password]):
            return False
            
        try:
            self.client = Client()
            self.client.login(handle, app_password)
            self.enabled = True
            logger.info("✓ Bluesky authenticated")
            return True
        except Exception as e:
            logger.warning(f"✗ Bluesky authentication failed: {e}")
            return False
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
            
        try:
            # Import models and TextBuilder for rich text with auto-detected facets
            from atproto import models, client_utils
            import re
            
            # Use TextBuilder to create rich text with explicit links
            text_builder = client_utils.TextBuilder()
            
            # Parse message to find URLs and convert them to clickable links
            # Pattern matches http:// and https:// URLs
            url_pattern = r'https?://[^\s]+'
            last_pos = 0
            first_url = None  # Track first URL for embed card
            
            for match in re.finditer(url_pattern, message):
                # Add text before URL
                if match.start() > last_pos:
                    text_builder.text(message[last_pos:match.start()])
                
                # Add URL as clickable link
                url = match.group()
                text_builder.link(url, url)
                
                # Capture first URL for embed card
                if first_url is None:
                    first_url = url
                
                last_pos = match.end()
            
            # Add any remaining text after last URL
            if last_pos < len(message):
                text_builder.text(message[last_pos:])
            
            # Create embed card for the first URL if found
            embed = None
            if first_url:
                try:
                    # Special handling for Kick with stream_data - use provided metadata
                    if 'kick.com/' in first_url and stream_data:
                        logger.info(f"ℹ Using stream metadata for Kick embed (CloudFlare bypass)")
                        
                        title = stream_data.get('title', 'Live on Kick')
                        thumbnail_url = stream_data.get('thumbnail_url')
                        
                        # Upload thumbnail to Bluesky if available
                        thumb_blob = None
                        if thumbnail_url:
                            try:
                                import requests
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                }
                                img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                                if img_response.status_code == 200:
                                    upload_response = self.client.upload_blob(img_response.content)
                                    thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                            except Exception as img_error:
                                logger.warning(f"⚠ Could not upload Kick thumbnail: {img_error}")
                        
                        # Create external embed with stream metadata (no viewer count to avoid showing 0 at start)
                        game_name = stream_data.get('game_name', '')
                        description = f"🔴 LIVE"
                        if game_name:
                            description += f" • {game_name}"
                        
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else 'Live on Kick',
                                description=description[:1000],
                                thumb=thumb_blob if thumb_blob else None
                            )
                        )
                    elif 'kick.com/' in first_url:
                        # Kick.com without stream_data - blocks automated requests with CloudFlare security policies
                        # Links will still be clickable, just without embed cards
                        logger.info(f"ℹ Kick.com blocks automated requests, posting with clickable link only")
                        embed = None
                    elif stream_data and ('twitch.tv/' in first_url or 'youtube.com/' in first_url or 'youtu.be/' in first_url):
                        # Use stream_data for Twitch/YouTube if available (more reliable than scraping)
                        logger.info(f"ℹ Using stream metadata for embed")
                        
                        title = stream_data.get('title', 'Live Stream')
                        thumbnail_url = stream_data.get('thumbnail_url')
                        
                        # Upload thumbnail to Bluesky if available
                        thumb_blob = None
                        if thumbnail_url:
                            try:
                                import requests
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                }
                                img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                                if img_response.status_code == 200:
                                    upload_response = self.client.upload_blob(img_response.content)
                                    thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                            except Exception as img_error:
                                logger.warning(f"⚠ Could not upload thumbnail: {img_error}")
                        
                        # Create external embed with stream metadata (no viewer count to avoid showing 0 at start)
                        game_name = stream_data.get('game_name', '')
                        description = f"🔴 LIVE"
                        if game_name:
                            description += f" • {game_name}"
                        
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else 'Live Stream',
                                description=description[:1000],
                                thumb=thumb_blob if thumb_blob else None
                            )
                        )
                    else:
                        # For non-Kick URLs, scrape Open Graph metadata
                        import requests
                        from bs4 import BeautifulSoup
                        
                        # Fetch the page with a realistic browser User-Agent
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                        }
                        
                        response = requests.get(first_url, headers=headers, timeout=10)
                        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Try Open Graph metadata first
                        og_title = soup.find('meta', property='og:title')
                        og_description = soup.find('meta', property='og:description')
                        og_image = soup.find('meta', property='og:image')
                        
                        # Fallback to Twitter Card metadata if OG tags not found
                        if not og_title:
                            og_title = soup.find('meta', attrs={'name': 'twitter:title'})
                        if not og_description:
                            og_description = soup.find('meta', attrs={'name': 'twitter:description'})
                        if not og_image:
                            og_image = soup.find('meta', attrs={'name': 'twitter:image'})
                        
                        title = og_title['content'] if og_title and og_title.get('content') else first_url
                        description = og_description['content'] if og_description and og_description.get('content') else ''
                        image_url = og_image['content'] if og_image and og_image.get('content') else None
                        
                        # Upload image to Bluesky if available
                        thumb_blob = None
                        if image_url:
                            try:
                                # Handle relative URLs
                                if image_url.startswith('//'):
                                    image_url = 'https:' + image_url
                                elif image_url.startswith('/'):
                                    from urllib.parse import urlparse
                                    parsed = urlparse(first_url)
                                    image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"
                                
                                img_response = requests.get(image_url, headers=headers, timeout=10)
                                if img_response.status_code == 200:
                                    # Upload image as blob and extract the blob reference
                                    from atproto import models
                                    upload_response = self.client.upload_blob(img_response.content)
                                    # The upload_blob returns a Response object with a blob attribute
                                    thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                            except Exception as img_error:
                                logger.warning(f"⚠ Could not upload thumbnail: {img_error}")
                        
                        # Create external embed with metadata
                        from atproto import models
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else first_url,  # Limit title length
                                description=description[:1000] if description else '',  # Limit description length
                                thumb=thumb_blob if thumb_blob else None
                            )
                        )
                except Exception as embed_error:
                    logger.warning(f"⚠ Could not create embed card: {embed_error}")
                    embed = None
            
            if reply_to_id:
                # Threading on Bluesky requires parent and root references
                try:
                    # Get the parent post details
                    parent_response = self.client.app.bsky.feed.get_posts({'uris': [reply_to_id]})
                    
                    if not parent_response or not hasattr(parent_response, 'posts') or not parent_response.posts:
                        logger.warning(f"⚠ Could not fetch parent post, posting without thread")
                        response = self.client.send_post(text_builder, embed=embed)
                        return response.uri if hasattr(response, 'uri') else None
                    
                    parent_post = parent_response.posts[0]
                    
                    # Determine root: if parent has a reply, use its root, otherwise parent is root
                    if hasattr(parent_post.record, 'reply') and parent_post.record.reply:
                        root_ref = parent_post.record.reply.root
                    else:
                        # Parent is the root - create strong ref
                        root_ref = models.create_strong_ref(parent_post)
                    
                    # Create parent reference
                    parent_ref = models.create_strong_ref(parent_post)
                    
                    # Create reply reference
                    reply_ref = models.AppBskyFeedPost.ReplyRef(
                        parent=parent_ref,
                        root=root_ref
                    )
                    
                    # Send threaded post with rich text and embed
                    response = self.client.send_post(text_builder, reply_to=reply_ref, embed=embed)
                    return response.uri if hasattr(response, 'uri') else None
                    
                except Exception as thread_error:
                    logger.warning(f"⚠ Bluesky threading failed, posting without thread: {thread_error}")
                    # Fall back to non-threaded post
                    response = self.client.send_post(text_builder, embed=embed)
                    return response.uri if hasattr(response, 'uri') else None
            else:
                # Simple post without threading, with rich text and embed card
                response = self.client.send_post(text_builder, embed=embed)
                return response.uri if hasattr(response, 'uri') else None
                
        except Exception as e:
            logger.error(f"✗ Bluesky post failed: {e}")
            return None


class DiscordPlatform(SocialPlatform):
    """Discord webhook platform with flexible per-platform webhook and role support."""
    
    def __init__(self):
        super().__init__("Discord")
        self.webhook_url = None  # Default webhook
        self.webhook_urls = {}  # platform_name -> webhook_url mapping
        self.role_id = None  # Default role
        self.role_mentions = {}  # platform_name -> role_id mapping
        self.active_messages = {}  # platform_name -> {message_id, webhook_url, last_update} tracking
        
    def authenticate(self):
        if not get_bool_config('Discord', 'enable_posting', default=False):
            return False
        
        # Get default webhook URL
        self.webhook_url = get_secret('Discord', 'webhook_url',
                                      secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                      secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                      doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
        
        # Get per-platform webhook URLs (optional - overrides default)
        for platform in ['twitch', 'youtube', 'kick']:
            platform_webhook = get_secret('Discord', f'webhook_{platform}',
                                         secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                         secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                         doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
            if platform_webhook:
                self.webhook_urls[platform] = platform_webhook
                logger.info(f"  • Discord webhook configured for {platform.upper()}")
        
        # Need at least one webhook (default or per-platform)
        if not self.webhook_url and not self.webhook_urls:
            return False
        
        # Get default role ID (optional)
        self.role_id = get_secret('Discord', 'role',
                                 secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                 secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                 doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
        
        # Get per-platform role IDs (optional - overrides default)
        for platform in ['twitch', 'youtube', 'kick']:
            platform_role = get_secret('Discord', f'role_{platform}',
                                      secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                      secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                      doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
            if platform_role:
                self.role_mentions[platform] = platform_role
                logger.info(f"  • Discord role configured for {platform.upper()}: {platform_role}")
        
        self.enabled = True
        if self.webhook_url:
            logger.info("✓ Discord webhook configured (default)")
        if self.webhook_urls:
            logger.info(f"✓ Discord webhooks configured ({len(self.webhook_urls)} platform-specific)")
        return True
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        # Determine which webhook to use for this platform
        webhook_url = None
        if platform_name and platform_name.lower() in self.webhook_urls:
            # Use platform-specific webhook if available
            webhook_url = self.webhook_urls[platform_name.lower()]
        else:
            # Fall back to default webhook
            webhook_url = self.webhook_url
        
        if not webhook_url:
            logger.warning(f"⚠ No Discord webhook configured for {platform_name or 'default'}")
            return None
            
        try:
            import re
            
            # Extract URL from message for embed
            url_pattern = r'https?://[^\s]+'
            url_match = re.search(url_pattern, message)
            first_url = url_match.group() if url_match else None
            
            # Build Discord embed with rich card
            embed = None
            if first_url and stream_data:
                # Determine color and platform info from URL
                color = 0x9146FF  # Default purple
                platform_title = "Live Stream"
                
                if 'twitch.tv' in first_url:
                    color = 0x9146FF  # Twitch purple
                    platform_title = "🟣 Live on Twitch"
                elif 'youtube.com' in first_url or 'youtu.be' in first_url:
                    color = 0xFF0000  # YouTube red
                    platform_title = "🔴 Live on YouTube"
                elif 'kick.com' in first_url:
                    color = 0x53FC18  # Kick green
                    platform_title = "🟢 Live on Kick"
                
                # Get stream data
                stream_title = stream_data.get('title', 'Live Stream')
                viewer_count = stream_data.get('viewer_count')
                thumbnail_url = stream_data.get('thumbnail_url')
                game_name = stream_data.get('game_name')
                
                embed = {
                    "title": platform_title,
                    "description": stream_title if stream_title else "Stream is live!",
                    "url": first_url,
                    "color": color,
                }
                
                # Add fields for viewer count and game if available
                fields = []
                if viewer_count is not None:
                    fields.append({
                        "name": "👥 Viewers",
                        "value": f"{viewer_count:,}",
                        "inline": True
                    })
                if game_name:
                    fields.append({
                        "name": "🎮 Category",
                        "value": game_name,
                        "inline": True
                    })
                
                if fields:
                    embed["fields"] = fields
                
                # Add thumbnail if available
                if thumbnail_url:
                    embed["image"] = {"url": thumbnail_url}
                
                embed["footer"] = {"text": "Click to watch the stream!"}
            
            # Build content: LLM message + role mention
            content = message  # Start with the LLM-generated message
            
            # Add role mention if configured for this platform
            if platform_name and platform_name.lower() in self.role_mentions:
                role_id = self.role_mentions[platform_name.lower()]
                content += f" <@&{role_id}>"
            elif self.role_id:
                # Use default role if no platform-specific role
                content += f" <@&{self.role_id}>"
            
            # Build webhook payload
            data = {}
            if content:
                data["content"] = content
            if embed:
                data["embeds"] = [embed]
            
            # Add ?wait=true to get the message ID back
            webhook_url_with_wait = webhook_url + "?wait=true" if "?" not in webhook_url else webhook_url + "&wait=true"
            
            response = requests.post(webhook_url_with_wait, json=data, timeout=10)
            
            if response.status_code == 200:
                # Store message info for future updates
                message_data = response.json()
                message_id = message_data.get('id')
                if message_id and platform_name:
                    import time
                    self.active_messages[platform_name.lower()] = {
                        'message_id': message_id,
                        'webhook_url': webhook_url,
                        'last_update': time.time(),
                        'original_content': content  # Store LLM message + role mention
                    }
                logger.info(f"✓ Discord embed posted (ID: {message_id})")
                return message_id
            else:
                logger.warning(f"⚠ Discord post failed with status {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"✗ Discord post failed: {e}")
            return None
    
    def update_stream(self, platform_name: str, stream_data: dict, stream_url: str) -> bool:
        """Update an existing Discord embed with fresh stream data (viewer count, thumbnail)."""
        if not self.enabled or not platform_name:
            return False
        
        platform_key = platform_name.lower()
        if platform_key not in self.active_messages:
            logger.debug(f"No active Discord message for {platform_name} to update")
            return False
        
        msg_info = self.active_messages[platform_key]
        message_id = msg_info['message_id']
        webhook_url = msg_info['webhook_url']
        
        try:
            import re
            import time
            
            # Determine color and platform info
            color = 0x9146FF  # Default purple
            platform_title = "Live Stream"
            
            if 'twitch.tv' in stream_url or platform_key == 'twitch':
                color = 0x9146FF
                platform_title = "🟣 Live on Twitch"
            elif 'youtube.com' in stream_url or 'youtu.be' in stream_url or platform_key == 'youtube':
                color = 0xFF0000
                platform_title = "🔴 Live on YouTube"
            elif 'kick.com' in stream_url or platform_key == 'kick':
                color = 0x53FC18
                platform_title = "🟢 Live on Kick"
            
            # Build updated embed
            stream_title = stream_data.get('title', 'Live Stream')
            viewer_count = stream_data.get('viewer_count')
            thumbnail_url = stream_data.get('thumbnail_url')
            game_name = stream_data.get('game_name')
            
            embed = {
                "title": platform_title,
                "description": stream_title,
                "url": stream_url,
                "color": color,
            }
            
            # Add fields for viewer count and game
            fields = []
            if viewer_count is not None:
                fields.append({
                    "name": "👥 Viewers",
                    "value": f"{viewer_count:,}",
                    "inline": True
                })
            if game_name:
                fields.append({
                    "name": "🎮 Category",
                    "value": game_name,
                    "inline": True
                })
            
            if fields:
                embed["fields"] = fields
            
            # Add thumbnail with cache-busting timestamp to force refresh
            if thumbnail_url:
                # Add timestamp to URL to force Discord to fetch new thumbnail
                separator = '&' if '?' in thumbnail_url else '?'
                embed["image"] = {"url": f"{thumbnail_url}{separator}_t={int(time.time())}"}
            
            # Add last updated timestamp in footer
            embed["footer"] = {"text": f"Last updated: {time.strftime('%H:%M:%S')} • Click to watch!"}
            
            # Keep original content (LLM message + role mention) from initial post
            content = msg_info.get('original_content', '')
            
            # Build update payload
            data = {}
            if content:
                data["content"] = content
            data["embeds"] = [embed]
            
            # PATCH the message via webhook
            edit_url = f"{webhook_url}/messages/{message_id}"
            response = requests.patch(edit_url, json=data, timeout=10)
            
            if response.status_code == 200:
                msg_info['last_update'] = time.time()
                logger.info(f"✓ Discord embed updated for {platform_name} (viewers: {viewer_count:,})" if viewer_count else f"✓ Discord embed updated for {platform_name}")
                return True
            else:
                logger.warning(f"⚠ Discord update failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Discord update failed: {e}")
            return False
    
    def clear_stream(self, platform_name: str) -> None:
        """Clear tracked message for a platform when stream ends."""
        platform_key = platform_name.lower()
        if platform_key in self.active_messages:
            del self.active_messages[platform_key]
            logger.debug(f"Cleared Discord message tracking for {platform_name}")
    
    def end_stream(self, platform_name: str, stream_data: dict, stream_url: str) -> bool:
        """Update Discord embed to show stream has ended, keeping VOD link and final stats."""
        if not self.enabled or not platform_name:
            return False
        
        platform_key = platform_name.lower()
        if platform_key not in self.active_messages:
            logger.debug(f"No active Discord message for {platform_name} to mark as ended")
            return False
        
        msg_info = self.active_messages[platform_key]
        message_id = msg_info['message_id']
        webhook_url = msg_info['webhook_url']
        
        try:
            import re
            import time
            
            # Get custom "stream ended" message from .env (configuration, NOT secrets)
            # These are user-facing messages, not sensitive data - they stay in .env
            ended_message = os.getenv(f'DISCORD_ENDED_MESSAGE_{platform_key.upper()}')
            
            if not ended_message:
                # Fall back to default ended message
                ended_message = os.getenv('DISCORD_ENDED_MESSAGE')
            
            if not ended_message:
                # Ultimate fallback if no config provided
                ended_message = "Thanks for joining! Tune in next time 💜"
            
            # Determine color and platform info (use muted colors for ended streams)
            color = 0x808080  # Gray for ended
            platform_title = "Stream Ended"
            
            if 'twitch.tv' in stream_url or platform_key == 'twitch':
                color = 0x6441A5  # Muted purple
                platform_title = "⏹️ Stream Ended - Twitch"
            elif 'youtube.com' in stream_url or 'youtu.be' in stream_url or platform_key == 'youtube':
                color = 0xCC0000  # Muted red
                platform_title = "⏹️ Stream Ended - YouTube"
            elif 'kick.com' in stream_url or platform_key == 'kick':
                color = 0x42C814  # Muted green
                platform_title = "⏹️ Stream Ended - Kick"
            
            # Build updated embed with ended message
            stream_title = stream_data.get('title', 'Stream')
            viewer_count = stream_data.get('viewer_count')
            thumbnail_url = stream_data.get('thumbnail_url')
            game_name = stream_data.get('game_name')
            
            embed = {
                "title": platform_title,
                "description": f"{ended_message}\n\n**{stream_title}**",
                "url": stream_url,  # Keep VOD link
                "color": color,
            }
            
            # Add fields for peak viewer count and game
            fields = []
            if viewer_count is not None:
                fields.append({
                    "name": "👥 Peak Viewers",
                    "value": f"{viewer_count:,}",
                    "inline": True
                })
            if game_name:
                fields.append({
                    "name": "🎮 Category",
                    "value": game_name,
                    "inline": True
                })
            
            if fields:
                embed["fields"] = fields
            
            # Keep final thumbnail
            if thumbnail_url:
                embed["image"] = {"url": thumbnail_url}
            
            # Add ended timestamp in footer
            embed["footer"] = {"text": f"Stream ended at {time.strftime('%H:%M:%S')} • Click for VOD"}
            
            # Keep role mention visible but don't ping again
            content = ""
            if platform_key in self.role_mentions:
                role_id = self.role_mentions[platform_key]
                content = f"<@&{role_id}>"
            elif self.role_id:
                content = f"<@&{self.role_id}>"
            
            # Build update payload
            data = {}
            if content:
                data["content"] = content
            data["embeds"] = [embed]
            
            # PATCH the message via webhook
            edit_url = f"{webhook_url}/messages/{message_id}"
            response = requests.patch(edit_url, json=data, timeout=10)
            
            if response.status_code == 200:
                # Clear tracking after successful update
                del self.active_messages[platform_key]
                logger.info(f"✓ Discord embed updated to show {platform_name} stream ended")
                return True
            else:
                logger.warning(f"⚠ Discord stream ended update failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Discord stream ended update failed: {e}")
            return False


class MatrixPlatform(SocialPlatform):
    """
    Matrix platform with rich message support.
    
    NOTE: Matrix does NOT support editing messages like Discord.
    Messages are posted once and cannot be updated with live viewer counts.
    """
    
    def __init__(self):
        super().__init__("Matrix")
        self.homeserver = None
        self.access_token = None
        self.room_id = None
        self.username = None
        self.password = None
        
    def authenticate(self):
        if not get_bool_config('Matrix', 'enable_posting', default=False):
            return False
        
        # Get homeserver (required)
        self.homeserver = get_secret('Matrix', 'homeserver',
                                     secret_name_env='SECRETS_AWS_MATRIX_SECRET_NAME',
                                     secret_path_env='SECRETS_VAULT_MATRIX_SECRET_PATH',
                                     doppler_secret_env='SECRETS_DOPPLER_MATRIX_SECRET_NAME')
        
        # Get room ID (required)
        self.room_id = get_secret('Matrix', 'room_id',
                                  secret_name_env='SECRETS_AWS_MATRIX_SECRET_NAME',
                                  secret_path_env='SECRETS_VAULT_MATRIX_SECRET_PATH',
                                  doppler_secret_env='SECRETS_DOPPLER_MATRIX_SECRET_NAME')
        
        if not self.homeserver or not self.room_id:
            return False
        
        # Ensure homeserver has proper format
        if not self.homeserver.startswith('http'):
            self.homeserver = f"https://{self.homeserver}"
        
        # Check for username/password first (preferred for bot accounts with auto-rotation)
        self.username = get_secret('Matrix', 'username',
                                   secret_name_env='SECRETS_AWS_MATRIX_SECRET_NAME',
                                   secret_path_env='SECRETS_VAULT_MATRIX_SECRET_PATH',
                                   doppler_secret_env='SECRETS_DOPPLER_MATRIX_SECRET_NAME')
        
        self.password = get_secret('Matrix', 'password',
                                   secret_name_env='SECRETS_AWS_MATRIX_SECRET_NAME',
                                   secret_path_env='SECRETS_VAULT_MATRIX_SECRET_PATH',
                                   doppler_secret_env='SECRETS_DOPPLER_MATRIX_SECRET_NAME')
        
        # Priority: Username/Password > Access Token
        # If both are set, username/password takes precedence for automatic token rotation
        if self.username and self.password:
            # Login to get fresh access token
            logger.info("Using username/password authentication (auto-rotation enabled)")
            self.access_token = self._login_and_get_token()
            if not self.access_token:
                logger.error("✗ Matrix login failed - check username/password")
                return False
            logger.info(f"✓ Matrix logged in and obtained access token")
        else:
            # Fall back to static access token
            logger.info("Using static access token authentication")
            self.access_token = get_secret('Matrix', 'access_token',
                                           secret_name_env='SECRETS_AWS_MATRIX_SECRET_NAME',
                                           secret_path_env='SECRETS_VAULT_MATRIX_SECRET_PATH',
                                           doppler_secret_env='SECRETS_DOPPLER_MATRIX_SECRET_NAME')
            
            if not self.access_token:
                logger.error("✗ Matrix authentication failed - need either access_token OR username+password")
                return False
        
        self.enabled = True
        logger.info(f"✓ Matrix authenticated ({self.room_id})")
        return True
    
    def _login_and_get_token(self):
        """Login with username/password to get access token."""
        try:
            # Extract just the username part from full MXID (@username:domain)
            # Matrix login expects just "username", not "@username:domain"
            username_local = self.username
            if username_local.startswith('@'):
                # Remove @ prefix and :domain suffix
                username_local = username_local[1:].split(':')[0]
            
            login_url = f"{self.homeserver}/_matrix/client/r0/login"
            login_data = {
                "type": "m.login.password",
                "identifier": {
                    "type": "m.id.user",
                    "user": username_local
                },
                "password": self.password
            }
            
            response = requests.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                if access_token:
                    logger.info(f"✓ Obtained Matrix access token (expires: {data.get('expires_in_ms', 'never')})")
                    logger.debug(f"Token starts with: {access_token[:20]}...")
                    return access_token
                else:
                    logger.error(f"✗ Matrix login succeeded but no access_token in response: {data}")
            else:
                logger.error(f"✗ Matrix login failed: {response.status_code} - {response.text}")
            
            return None
        except Exception as e:
            logger.error(f"✗ Matrix login error: {e}")
            return None
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled:
            logger.debug(f"⚠ Matrix post skipped: disabled (enabled={self.enabled})")
            return None
        if not all([self.homeserver, self.access_token, self.room_id]):
            logger.warning(f"⚠ Matrix post skipped: missing credentials (homeserver={bool(self.homeserver)}, token={bool(self.access_token)}, room={bool(self.room_id)})")
            return None
            
        try:
            import re
            from urllib.parse import quote
            
            # Extract URL from message for rich formatting
            url_pattern = r'https?://[^\s]+'
            url_match = re.search(url_pattern, message)
            first_url = url_match.group() if url_match else None
            
            # Create rich HTML message with link preview
            html_body = message
            plain_body = message
            
            if first_url:
                # Make URL clickable in HTML
                html_body = re.sub(url_pattern, f'<a href="{first_url}">{first_url}</a>', message)
                
                # Add platform-specific styling
                if 'twitch.tv' in first_url:
                    html_body = f'<p><strong>🟣 Live on Twitch!</strong></p><p>{html_body}</p>'
                elif 'youtube.com' in first_url or 'youtu.be' in first_url:
                    html_body = f'<p><strong>🔴 Live on YouTube!</strong></p><p>{html_body}</p>'
                elif 'kick.com' in first_url:
                    html_body = f'<p><strong>🟢 Live on Kick!</strong></p><p>{html_body}</p>'
            
            # Build Matrix message event
            event_data = {
                "msgtype": "m.text",
                "body": plain_body,
                "format": "org.matrix.custom.html",
                "formatted_body": html_body
            }
            
            # Add reply reference if provided
            if reply_to_id:
                event_data["m.relates_to"] = {
                    "m.in_reply_to": {
                        "event_id": reply_to_id
                    }
                }
            
            # Send message via Matrix Client-Server API
            url = f"{self.homeserver}/_matrix/client/r0/rooms/{quote(self.room_id)}/send/m.room.message"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=event_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event_id = data.get('event_id')
                logger.info(f"✓ Matrix message posted")
                return event_id
            else:
                logger.warning(f"⚠ Matrix post failed with status {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"✗ Matrix post failed: {e}")
            return None


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
