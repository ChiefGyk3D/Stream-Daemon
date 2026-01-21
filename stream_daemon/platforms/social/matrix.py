"""
Matrix platform implementation with rich message support.

NOTE: Matrix does NOT support editing messages like Discord.
Messages are posted once and cannot be updated with live viewer counts.

Matrix: Because Discord was too centralized, Mastodon was too ActivityPub,
and IRC was too... 1988. So we created a federated chat protocol where your
server talks to other servers through a distributed network using JSON over HTTPS
to eventually, somewhere, somehow, deliver the groundbreaking news that you're playing Minecraft.

The future of decentralized communication: now with 300% more JSON, 500% more complexity,
and 0% more actual functionality than IRC had in 1988. But hey, at least we can send emojis.
Fucking emojis. That's what we needed to solve. Not world hunger, not climate change - emojis.
"""

import logging
import re
from typing import Optional
from urllib.parse import quote, urlparse
import requests
from stream_daemon.config import get_bool_config, get_secret

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
    """
    
    def __init__(self):
        self.name = "Matrix"
        self.enabled = False
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
                    return access_token
                else:
                    logger.error(f"✗ Matrix login succeeded but no access_token in response")
            else:
                logger.error(f"✗ Matrix login failed: {response.status_code}")
            
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
