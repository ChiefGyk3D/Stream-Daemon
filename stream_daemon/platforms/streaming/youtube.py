"""YouTube Live streaming platform integration."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from googleapiclient.discovery import build

from stream_daemon.config import get_config, get_secret
from stream_daemon.platforms.base import StreamingPlatform

logger = logging.getLogger(__name__)


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
        
    def authenticate(self) -> bool:
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
    
    def _get_channel_id_from_username(self) -> Optional[str]:
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
    
    def is_live(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
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
    
    def _resolve_channel_id(self, username: str) -> Optional[str]:
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
