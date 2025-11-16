"""
Matrix platform implementation with rich message support.

NOTE: Matrix does NOT support editing messages like Discord.
Messages are posted once and cannot be updated with live viewer counts.
"""

import logging
import re
from typing import Optional
from urllib.parse import quote, urlparse
import requests
from stream_daemon.config import get_bool_config, get_secret
from stream_daemon.config.constants import (
    SECRETS_AWS_MATRIX_SECRET_NAME,
    SECRETS_VAULT_MATRIX_SECRET_PATH,
    SECRETS_DOPPLER_MATRIX_SECRET_NAME
)

logger = logging.getLogger(__name__)


def _is_url_for_domain(url: str, domain: str) -> bool:
    """
    Safely check if a URL is for a specific domain.
    
    Args:
        url: The URL to check
        domain: The domain to match (e.g., 'kick.com', 'twitch.tv')
    
    Returns:
        True if the URL's hostname matches or is a subdomain of the domain
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Normalize to lowercase for comparison
        hostname = hostname.lower()
        domain = domain.lower()
        
        # Check exact match
        if hostname == domain:
            return True
        
        # Check if it's a proper subdomain (must end with .domain, not just contain domain)
        # This prevents eviltwitch.tv from matching twitch.tv
        if hostname.endswith('.' + domain):
            # Ensure there's no additional dot after the subdomain
            # e.g., www.twitch.tv is valid, but not twitch.tv.evil.com
            return True
        
        return False
    except Exception:
        return False


class MatrixPlatform:
    """
    Matrix platform with rich message support.
    
    NOTE: Matrix does NOT support editing messages like Discord.
    Messages are posted once and cannot be updated with live viewer counts.
    
    Supports per-username configuration for multi-streamer monitoring.
    Each streamer can post to a different Matrix room (same or different homeserver).
    """
    
    def __init__(self):
        self.name = "Matrix"
        self.enabled = False
        self.homeserver = None
        self.access_token = None
        self.room_id = None
        self.username = None
        self.password = None
        self.configs_per_user = {}  # "platform_username" -> {homeserver, access_token, room_id} dict
        
    def authenticate(self):
        if not get_bool_config('Matrix', 'enable_posting', default=False):
            return False
        
        # Get homeserver (required)
        self.homeserver = get_secret('Matrix', 'homeserver',
                                     secret_name_env=SECRETS_AWS_MATRIX_SECRET_NAME,
                                     secret_path_env=SECRETS_VAULT_MATRIX_SECRET_PATH,
                                     doppler_secret_env=SECRETS_DOPPLER_MATRIX_SECRET_NAME)
        
        # Get room ID (required)
        self.room_id = get_secret('Matrix', 'room_id')
        
        if not self.homeserver or not self.room_id:
            return False
        
        # Ensure homeserver has proper format
        if not self.homeserver.startswith('http'):
            self.homeserver = f"https://{self.homeserver}"
        
        # Check for username/password first (preferred for bot accounts with auto-rotation)
        self.username = get_secret('Matrix', 'username')
        
        self.password = get_secret('Matrix', 'password')
        
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
            self.access_token = get_secret('Matrix', 'access_token')
            
            if not self.access_token:
                logger.error("✗ Matrix authentication failed - need either access_token OR username+password")
                return False
        
        self.enabled = True
        logger.info(f"✓ Matrix authenticated (default room: {self.room_id})")
        logger.info("  Per-username rooms supported (MATRIX_ROOM_ID_PLATFORM_USERNAME)")
        return True
    
    def _login_and_get_token(self):
        """Login with username/password to get access token (for default account)."""
        return self._login_and_get_token_for_user(self.homeserver, self.username, self.password)
    
    def _login_and_get_token_for_user(self, homeserver, username, password):
        """Login with username/password to get access token (for any account)."""
        try:
            # Extract just the username part from full MXID (@username:domain)
            # Matrix login expects just "username", not "@username:domain"
            username_local = username
            if username_local.startswith('@'):
                # Remove @ prefix and :domain suffix
                username_local = username_local[1:].split(':')[0]
            
            login_url = f"{homeserver}/_matrix/client/r0/login"
            login_data = {
                "type": "m.login.password",
                "identifier": {
                    "type": "m.id.user",
                    "user": username_local
                },
                "password": password
            }
            
            response = requests.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                if access_token:
                    logger.info(f"✓ Obtained Matrix access token (expires: {data.get('expires_in_ms', 'never')})")
                    return access_token
                else:
                    logger.error(f"✗ Matrix login succeeded but no access_token in response")
            else:
                logger.error(f"✗ Matrix login failed: {response.status_code}")
            
            return None
        except Exception as e:
            logger.error(f"✗ Matrix login error: {e}")
            return None
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None, username: Optional[str] = None) -> Optional[str]:
        if not self.enabled:
            logger.debug(f"⚠ Matrix post skipped: disabled (enabled={self.enabled})")
            return None
        
        # Determine which configuration to use (per-username > default)
        homeserver = None
        access_token = None
        room_id = None
        lookup_key = None
        
        if platform_name and username:
            # Try per-username configuration first
            lookup_key = f"{platform_name.lower()}_{username.lower()}"
            
            # Check if we've already loaded this user's config
            if lookup_key in self.configs_per_user:
                config = self.configs_per_user[lookup_key]
                homeserver = config['homeserver']
                access_token = config['access_token']
                room_id = config['room_id']
                logger.debug(f"Using cached per-user Matrix config for {platform_name}/{username}")
            else:
                # Try to dynamically load per-username configuration
                # Build dynamic secret env names for per-username configs
                secret_suffix = f"_{lookup_key.upper()}_SECRET_NAME"
                path_suffix = f"_{lookup_key.upper()}_SECRET_PATH"
                aws_secret = f"{SECRETS_AWS_MATRIX_SECRET_NAME.replace('_SECRET_NAME', '')}{secret_suffix}"
                vault_secret = f"{SECRETS_VAULT_MATRIX_SECRET_PATH.replace('_SECRET_PATH', '')}{path_suffix}"
                doppler_secret = f"{SECRETS_DOPPLER_MATRIX_SECRET_NAME.replace('_SECRET_NAME', '')}{secret_suffix}"
                
                user_homeserver = get_secret('Matrix', f'homeserver_{lookup_key}',
                                            secret_name_env=aws_secret,
                                            secret_path_env=vault_secret,
                                            doppler_secret_env=doppler_secret)
                user_room_id = get_secret('Matrix', f'room_id_{lookup_key}',
                                         secret_name_env=aws_secret,
                                         secret_path_env=vault_secret,
                                         doppler_secret_env=doppler_secret)
                
                if user_homeserver and user_room_id:
                    # Ensure homeserver has proper format
                    if not user_homeserver.startswith('http'):
                        user_homeserver = f"https://{user_homeserver}"
                    
                    # Check for username/password (preferred)
                    # Reuse the same secret env names for all per-user Matrix secrets
                    user_username = get_secret('Matrix', f'username_{lookup_key}',
                                              secret_name_env=aws_secret,
                                              secret_path_env=vault_secret,
                                              doppler_secret_env=doppler_secret)
                    user_password = get_secret('Matrix', f'password_{lookup_key}',
                                              secret_name_env=aws_secret,
                                              secret_path_env=vault_secret,
                                              doppler_secret_env=doppler_secret)
                    
                    user_access_token = None
                    if user_username and user_password:
                        # Login to get fresh access token
                        logger.info(f"Loading per-user Matrix account for {platform_name}/{username} (username/password)")
                        user_access_token = self._login_and_get_token_for_user(user_homeserver, user_username, user_password)
                        if not user_access_token:
                            logger.warning(f"⚠ Per-user Matrix login failed for {platform_name}/{username}")
                    else:
                        # Fall back to static access token
                        user_access_token = get_secret('Matrix', f'access_token_{lookup_key}',
                                                       secret_name_env=aws_secret,
                                                       secret_path_env=vault_secret,
                                                       doppler_secret_env=doppler_secret)
                    
                    if user_access_token:
                        # Cache the configuration
                        self.configs_per_user[lookup_key] = {
                            'homeserver': user_homeserver,
                            'access_token': user_access_token,
                            'room_id': user_room_id
                        }
                        homeserver = user_homeserver
                        access_token = user_access_token
                        room_id = user_room_id
                        logger.info(f"✓ Per-user Matrix authenticated for {platform_name}/{username} (room: {room_id})")
                    else:
                        logger.warning(f"⚠ Per-user Matrix configuration incomplete for {platform_name}/{username}")
                        logger.info(f"  Falling back to default Matrix room")
        
        # Fallback to default configuration if no per-username config found
        if not all([homeserver, access_token, room_id]):
            homeserver = self.homeserver
            access_token = self.access_token
            room_id = self.room_id
            if not all([homeserver, access_token, room_id]):
                logger.warning(f"⚠ Matrix post skipped: missing credentials (homeserver={bool(homeserver)}, token={bool(access_token)}, room={bool(room_id)})")
                return None
            
        try:
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
                if _is_url_for_domain(first_url, 'twitch.tv'):
                    html_body = f'<p><strong>🟣 Live on Twitch!</strong></p><p>{html_body}</p>'
                elif _is_url_for_domain(first_url, 'youtube.com') or _is_url_for_domain(first_url, 'youtu.be'):
                    html_body = f'<p><strong>🔴 Live on YouTube!</strong></p><p>{html_body}</p>'
                elif _is_url_for_domain(first_url, 'kick.com'):
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
            url = f"{homeserver}/_matrix/client/r0/rooms/{quote(room_id)}/send/m.room.message"
            headers = {
                "Authorization": f"Bearer {access_token}",
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
