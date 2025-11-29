"""Kick streaming platform integration."""

import logging
from typing import Optional, Tuple

import requests

from stream_daemon.config import get_bool_config, get_secret
from stream_daemon.platforms.base import StreamingPlatform

logger = logging.getLogger(__name__)


class KickPlatform(StreamingPlatform):
    """Kick streaming platform with optional authentication."""
    
    def __init__(self):
        super().__init__("Kick")
        # Note: self.enabled is set to False in parent class
        self.access_token = None
        self.use_auth = False
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.error_cooldown_time = None  # Track when error cooldown started
        
    def authenticate(self) -> bool:
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
    
    def is_live(self, username: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if Kick stream is live.
        
        Args:
            username: Kick username to check
            
        Returns:
            tuple: (is_live, stream_data) or (False, None) on error
        """
        if not self.enabled:
            return False, None
        
        # Check if we're in error cooldown period (10 minutes after hitting max errors)
        if self.consecutive_errors >= self.max_consecutive_errors:
            if self.error_cooldown_time:
                from datetime import datetime, timedelta
                time_since_error = datetime.now() - self.error_cooldown_time
                if time_since_error < timedelta(minutes=10):
                    # Still in cooldown period
                    remaining_min = 10 - (time_since_error.seconds // 60)
                    logger.debug(f"Kick in error cooldown (cooldown: {remaining_min} min remaining)")
                    return False, None
                else:
                    # Cooldown expired, reset and try again
                    logger.info(f"Kick error cooldown expired, resetting error count and resuming checks")
                    self.consecutive_errors = 0
                    self.error_cooldown_time = None
            else:
                # First time hitting max errors - start cooldown
                from datetime import datetime
                self.error_cooldown_time = datetime.now()
                logger.warning(f"⚠ Kick disabled temporarily due to {self.consecutive_errors} consecutive errors (10 minute cooldown)")
                return False, None
        
        try:
            if self.use_auth and self.access_token:
                # Use official authenticated API
                return self._check_authenticated(username)
            else:
                # Fall back to public scraping API
                return self._check_public(username)
        except Exception as e:
            self.consecutive_errors += 1
            error_str = str(e)
            error_type = type(e).__name__
            
            logger.error(f"⚠ Error checking Kick/{username} ({error_type}): {e}")
            logger.error(f"   Consecutive errors: {self.consecutive_errors}/{self.max_consecutive_errors}")
            
            # Provide specific guidance based on error type
            if '401' in error_str or 'unauthorized' in error_str.lower():
                logger.error(f"   → 401 Unauthorized: OAuth token invalid or expired")
                logger.error(f"   → Re-authenticate or check KICK_CLIENT_ID/CLIENT_SECRET")
            elif '403' in error_str or 'forbidden' in error_str.lower():
                logger.error(f"   → 403 Forbidden: Check OAuth permissions")
            elif '404' in error_str or 'not found' in error_str.lower():
                logger.error(f"   → 404 Not Found: Channel '{username}' may not exist")
            elif 'timeout' in error_str.lower() or 'timed out' in error_str.lower():
                logger.error(f"   → Network timeout: Check internet connection and firewall settings")
            elif 'connection' in error_str.lower():
                logger.error(f"   → Connection error: Check network connectivity to kick.com")
            elif 'cloudflare' in error_str.lower() or 'captcha' in error_str.lower():
                logger.error(f"   → Cloudflare protection: May need OAuth authentication")
                logger.error(f"   → Set KICK_ENABLE_AUTH=True and configure OAuth")
            else:
                logger.error(f"   → Check Kick credentials and network configuration")
            
            if self.consecutive_errors >= self.max_consecutive_errors:
                logger.error(f"   ⏰ Kick will enter cooldown to prevent API abuse")
            
            return False, None
    
    def _check_authenticated(self, username: str) -> Tuple[bool, Optional[dict]]:
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
            
            # Reset error counter on success
            self.consecutive_errors = 0
            return True, stream_data

            
        except Exception as e:
            error_str = str(e)
            error_type = type(e).__name__
            logger.warning(f"Authenticated Kick check failed ({error_type}): {e}")
            
            # Provide specific guidance
            if '401' in error_str or 'unauthorized' in error_str.lower():
                logger.warning(f"   → OAuth token may be expired, falling back to public API")
            elif '403' in error_str or 'forbidden' in error_str.lower():
                logger.warning(f"   → API access forbidden, falling back to public API")
            else:
                logger.warning(f"   → Falling back to public API")
            
            return self._check_public(username)
    
    def _check_public(self, username: str) -> Tuple[bool, Optional[dict]]:
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
                        # Reset error counter on success
                        self.consecutive_errors = 0
                        return True, stream_data
            
            # Reset error counter even if offline (successful API call)
            self.consecutive_errors = 0
            return False, None
            
        except Exception as e:
            raise  # Re-raise to be caught by parent
