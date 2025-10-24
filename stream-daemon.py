"""
Stream Daemon - Universal streaming-to-social bridge
Monitors streaming platforms and posts to social media
Configuration via .env files and environment variables only
"""

from twitchAPI.twitch import Twitch
from mastodon import Mastodon
from atproto import Client
from googleapiclient.discovery import build
import time
import random
import hvac
import boto3
import os
import sys
import logging
import requests
from dopplersdk import DopplerSDK
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
import asyncio

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
# MESSAGE FILE PARSING
# ===========================================

def parse_sectioned_message_file(filepath: str) -> Dict[str, List[str]]:
    """
    Parse a message file with platform-specific sections.
    
    Format:
        [DEFAULT]
        message 1
        message 2
        
        [TWITCH]
        twitch message 1
        twitch message 2
        
        [YOUTUBE]
        youtube message 1
    
    Returns:
        Dict mapping platform name (or 'DEFAULT') to list of messages
    """
    sections = {}
    current_section = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Check if this is a section header
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].upper()
                    if current_section not in sections:
                        sections[current_section] = []
                    continue
                
                # Add message to current section
                if current_section:
                    sections[current_section].append(line)
    
    except FileNotFoundError:
        logger.warning(f"⚠ Message file not found: {filepath}")
        return {}
    
    return sections


# ===========================================
# STATE MANAGEMENT
# ===========================================

class StreamState(Enum):
    """States for stream lifecycle."""
    OFFLINE = "offline"
    LIVE = "live"
    
@dataclass
class StreamStatus:
    """Track the status of a streaming platform."""
    platform_name: str
    username: str
    state: StreamState = StreamState.OFFLINE
    title: Optional[str] = None
    went_live_at: Optional[datetime] = None
    last_check_live: bool = False
    consecutive_live_checks: int = 0
    consecutive_offline_checks: int = 0
    last_post_id: Optional[str] = None  # For threading replies
    
    def update(self, is_live: bool, title: Optional[str] = None) -> bool:
        """
        Update status based on current check.
        Returns True if state actually changed (offline->live or live->offline).
        Uses debouncing to avoid false positives from API hiccups.
        """
        if is_live:
            self.consecutive_live_checks += 1
            self.consecutive_offline_checks = 0
            
            # Require 2 consecutive live checks to confirm (debouncing)
            if self.state == StreamState.OFFLINE and self.consecutive_live_checks >= 2:
                self.state = StreamState.LIVE
                self.title = title
                self.went_live_at = datetime.now()
                self.last_post_id = None  # Reset threading for new stream
                logger.info(f"🔴 {self.platform_name}/{self.username} went LIVE: {title}")
                return True  # State changed!
            elif self.state == StreamState.LIVE:
                # Update title if changed
                if title and title != self.title:
                    logger.info(f"📝 {self.platform_name}/{self.username} updated title: {title}")
                    self.title = title
        else:
            self.consecutive_offline_checks += 1
            self.consecutive_live_checks = 0
            
            # Require 2 consecutive offline checks to confirm (debouncing)
            if self.state == StreamState.LIVE and self.consecutive_offline_checks >= 2:
                self.state = StreamState.OFFLINE
                duration = datetime.now() - self.went_live_at if self.went_live_at else None
                logger.info(f"🔵 {self.platform_name}/{self.username} went OFFLINE (duration: {duration})")
                self.title = None
                self.went_live_at = None
                return True  # State changed!
        
        return False  # No state change


# ===========================================
# SECRETS MANAGEMENT
# ===========================================

def load_secrets_from_aws(secret_name):
    """Load secrets from AWS Secrets Manager."""
    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Failed to load AWS secret {secret_name}: {e}")
        return {}

def load_secrets_from_vault(secret_path):
    """Load secrets from HashiCorp Vault."""
    try:
        vault_url = os.getenv('SECRETS_VAULT_URL')
        vault_token = os.getenv('SECRETS_VAULT_TOKEN')
        
        if not vault_url or not vault_token:
            logger.error("Vault URL or token not configured")
            return {}
        
        client = hvac.Client(url=vault_url, token=vault_token)
        if not client.is_authenticated():
            logger.error("Vault authentication failed")
            return {}
        
        response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        return response['data']['data']
    except Exception as e:
        logger.error(f"Failed to load Vault secret {secret_path}: {e}")
        return {}

def load_secrets_from_doppler(secret_name):
    """Load secrets from Doppler by secret name."""
    try:
        doppler_token = os.getenv('DOPPLER_TOKEN')
        if not doppler_token:
            logger.error("DOPPLER_TOKEN not set")
            return {}
        
        # Get Doppler project and config from environment
        doppler_project = os.getenv('DOPPLER_PROJECT', 'stream-daemon')
        doppler_config = os.getenv('DOPPLER_CONFIG', 'prd')
        
        sdk = DopplerSDK()
        sdk.set_access_token(doppler_token)
        
        # Fetch the specific secret from Doppler
        # Doppler stores secrets as key-value pairs in a project/config
        try:
            # Get all secrets from the specified project and config
            secrets_response = sdk.secrets.list(
                project=doppler_project,
                config=doppler_config
            )
            
            # Filter secrets that match our pattern
            # e.g., if secret_name is "twitch", look for TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
            secrets_dict = {}
            if hasattr(secrets_response, 'secrets'):
                all_keys = list(secrets_response.secrets.keys())
                logger.info(f"Doppler connection successful. Found {len(all_keys)} total secrets in project '{doppler_project}', config '{doppler_config}'")
                
                for secret_key, secret_value in secrets_response.secrets.items():
                    # Match secrets with the platform prefix
                    if secret_key.upper().startswith(secret_name.upper()):
                        # Extract the actual key name (e.g., CLIENT_ID from TWITCH_CLIENT_ID)
                        key_suffix = secret_key[len(secret_name)+1:].lower()  # +1 for underscore
                        secrets_dict[key_suffix] = secret_value.get('computed', secret_value.get('raw', ''))
                
                if not secrets_dict:
                    logger.info(f"No secrets found with prefix '{secret_name.upper()}_*'. Available secrets: {[k for k in all_keys if not k.startswith('DOPPLER_')]}")
            
            return secrets_dict
        except Exception as e:
            logger.error(f"Failed to fetch Doppler secret {secret_name}: {e}")
            return {}
            
    except Exception as e:
        logger.error(f"Failed to configure Doppler: {e}")
        return {}

def get_secret(platform, key, secret_name_env=None, secret_path_env=None, doppler_secret_env=None):
    """
    Get a secret value with priority:
    1. Environment variable (highest priority)
    2. Secrets manager (AWS/Vault/Doppler)
    3. None if not found
    
    Args:
        platform: Platform name (e.g., 'Twitch', 'YouTube')
        key: Secret key (e.g., 'client_id', 'api_key')
        secret_name_env: AWS Secrets Manager env var name
        secret_path_env: HashiCorp Vault env var name
        doppler_secret_env: Doppler secret name env var
    """
    # First check direct environment variable
    env_key = f"{platform.upper()}_{key.upper()}"
    env_value = os.getenv(env_key)
    if env_value:
        return env_value
    
    # Check which secrets manager is enabled
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    
    if secret_manager == 'aws' and secret_name_env:
        secret_name = os.getenv(secret_name_env)
        if secret_name:
            secrets = load_secrets_from_aws(secret_name)
            return secrets.get(key)
    
    elif secret_manager == 'vault' and secret_path_env:
        secret_path = os.getenv(secret_path_env)
        if secret_path:
            secrets = load_secrets_from_vault(secret_path)
            return secrets.get(key)
    
    elif secret_manager == 'doppler' and doppler_secret_env:
        secret_name = os.getenv(doppler_secret_env)
        if secret_name:
            secrets = load_secrets_from_doppler(secret_name)
            return secrets.get(key)
    
    return None


# ===========================================
# CONFIGURATION HELPERS
# ===========================================

def get_config(section, key, default=None):
    """Get config from environment variables only."""
    return os.getenv(f'{section.upper()}_{key.upper()}', default)

def get_bool_config(section, key, default=False):
    """Get boolean config from environment variables."""
    env_var = os.getenv(f'{section.upper()}_{key.upper()}')
    if env_var is not None:
        return env_var.lower() in ['true', '1', 't', 'y', 'yes']
    return default

def get_int_config(section, key, default=0):
    """Get integer config from environment variables."""
    env_var = os.getenv(f'{section.upper()}_{key.upper()}')
    if env_var is not None:
        return int(env_var)
    return default


# ===========================================
# STREAMING PLATFORM CLASSES
# ===========================================

class StreamingPlatform:
    """Base class for streaming platforms."""
    
    def __init__(self, name):
        self.name = name
        self.enabled = False
    
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
                        return True, live_streams[0].title
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
            # Try modern handle format first (@username)
            if self.username.startswith('@'):
                request = self.client.channels().list(
                    part="id",
                    forHandle=self.username
                )
            else:
                # Try legacy username format
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
        if not self.enabled or not self.client or not self.channel_id:
            return False, None
            
        try:
            request = self.client.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video",
                maxResults=1
            )
            response = request.execute()
            
            if response.get('items'):
                title = response['items'][0]['snippet']['title']
                return True, title
            return False, None
        except Exception as e:
            logger.error(f"Error checking YouTube: {e}")
            return False, None


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
        """Check stream status using authenticated API."""
        try:
            # Query channels by slug (username) - stream info is embedded in response
            url = "https://api.kick.com/public/v1/channels"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            params = {'slug': username}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Kick channel lookup failed: {response.status_code}")
                return False, None
            
            data = response.json()
            channels = data.get('data', [])
            
            if not channels:
                logger.warning(f"No channel found for username: {username}")
                return False, None
            
            channel = channels[0]
            
            # Check if stream is live (stream object is embedded in channel data)
            stream = channel.get('stream', {})
            is_live = stream.get('is_live', False)
            
            if is_live:
                # Title is at channel level, not stream level
                title = channel.get('stream_title', 'Live Stream')
                return True, title
            
            return False, None
            
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
                        return True, title
            
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
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
            
        try:
            # Post as a reply if reply_to_id is provided (threading)
            status = self.client.status_post(message, in_reply_to_id=reply_to_id)
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
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
            
        try:
            # Bluesky threading requires parent/root references
            # For now, simple posts - full threading implementation would need to track parent/root
            response = self.client.send_post(text=message)
            return response.uri if hasattr(response, 'uri') else None
        except Exception as e:
            logger.error(f"✗ Bluesky post failed: {e}")
            return None


class DiscordPlatform(SocialPlatform):
    """Discord webhook platform with role mention support."""
    
    def __init__(self):
        super().__init__("Discord")
        self.webhook_url = None
        self.role_mentions = {}  # platform_name -> role_id mapping
        
    def authenticate(self):
        if not get_bool_config('Discord', 'enable_posting', default=False):
            return False
            
        self.webhook_url = get_secret('Discord', 'webhook_url',
                                      secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                      secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                      doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
        
        if not self.webhook_url:
            return False
        
        # Load role mentions for each platform (optional)
        # Format: DISCORD_ROLE_TWITCH=1234567890
        for platform in ['TWITCH', 'YOUTUBE', 'KICK']:
            role_id = os.getenv(f'DISCORD_ROLE_{platform}')
            if role_id:
                self.role_mentions[platform.lower()] = role_id
                logger.info(f"  • Discord role configured for {platform}: {role_id}")
            
        self.enabled = True
        logger.info("✓ Discord webhook configured")
        return True
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None) -> Optional[str]:
        if not self.enabled or not self.webhook_url:
            return None
            
        try:
            # Add role mention if configured for this platform
            full_message = message
            if platform_name and platform_name.lower() in self.role_mentions:
                role_id = self.role_mentions[platform_name.lower()]
                full_message = f"<@&{role_id}> {message}"
            
            data = {"content": full_message}
            response = requests.post(self.webhook_url, json=data, timeout=10)
            
            if response.status_code == 204:
                return "discord_message"  # Discord webhooks don't return IDs easily
            return None
        except Exception as e:
            logger.error(f"✗ Discord post failed: {e}")
            return None


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
        DiscordPlatform()
    ]
    
    enabled_social = []
    for platform in social_platforms:
        if platform.authenticate():
            enabled_social.append(platform)
    
    if not enabled_social:
        logger.error("✗ No social platforms configured!")
        logger.error("   Enable at least one: Mastodon, Bluesky, or Discord")
        sys.exit(1)
    
    # Load messages from consolidated files with platform sections
    messages_file = get_config('Messages', 'messages_file', default='messages.txt')
    end_messages_file = get_config('Messages', 'end_messages_file', default='end_messages.txt')
    post_end_stream_message = get_bool_config('Messages', 'post_end_stream_message', default=True)
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
    
    logger.info("="*60)
    logger.info(f"📺 Monitoring: {', '.join([f'{s.platform_name}/{s.username}' for s in stream_statuses.values()])}")
    logger.info(f"📱 Posting to: {', '.join([p.name for p in enabled_social])}")
    logger.info(f"⏰ Check: {check_interval}min (offline) / {post_interval}min (live)")
    logger.info("="*60)
    
    # Main loop with improved state tracking
    while True:
        try:
            logger.info("🔍 Checking streams...")
            
            # Check all streaming platforms
            for platform in enabled_streaming:
                status = stream_statuses.get(platform.name)
                if not status:
                    continue
                
                # Check if stream is live
                is_live, stream_title = platform.is_live(status.username)
                
                # Update status and check if state changed
                state_changed = status.update(is_live, stream_title)
                
                if state_changed:
                    if status.state == StreamState.LIVE:
                        # Stream just went live - post to all social platforms
                        # Use platform-specific messages
                        platform_messages = messages.get(status.platform_name, [])
                        if not platform_messages:
                            logger.error(f"✗ No messages configured for {status.platform_name}")
                            continue
                        
                        message = random.choice(platform_messages).format(
                            stream_title=status.title,
                            username=status.username,
                            platform=status.platform_name
                        )
                        
                        logger.info(f"📢 Posting 'LIVE' announcement for {status.platform_name}/{status.username}")
                        
                        # Post to each social platform and track post IDs for threading
                        posted_count = 0
                        for social in enabled_social:
                            post_id = social.post(
                                message, 
                                reply_to_id=None,  # First post is never a reply
                                platform_name=status.platform_name
                            )
                            if post_id:
                                posted_count += 1
                                # Save first post ID for potential threading
                                if not status.last_post_id:
                                    status.last_post_id = post_id
                                logger.debug(f"  ✓ Posted to {social.name} (ID: {post_id})")
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted to {posted_count}/{len(enabled_social)} platform(s)")
                        else:
                            logger.warning(f"⚠ Failed to post to any platforms")
                    
                    elif status.state == StreamState.OFFLINE:
                        # Stream just ended - post end message if configured
                        platform_end_messages = end_messages.get(status.platform_name, [])
                        if post_end_stream_message and platform_end_messages:
                            message = random.choice(platform_end_messages).format(
                                username=status.username,
                                platform=status.platform_name
                            )
                            
                            logger.info(f"📢 Posting 'OFFLINE' announcement for {status.platform_name}/{status.username}")
                            
                            posted_count = 0
                            for social in enabled_social:
                                # Thread the end message as a reply to the live announcement
                                post_id = social.post(
                                    message,
                                    reply_to_id=status.last_post_id,  # Thread it!
                                    platform_name=status.platform_name
                                )
                                if post_id:
                                    posted_count += 1
                                    logger.debug(f"  ✓ Posted end message to {social.name}")
                            
                            if posted_count > 0:
                                logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
                else:
                    # No state change - just log current status
                    if status.state == StreamState.LIVE:
                        logger.debug(f"  {status.platform_name}/{status.username}: Still live ({status.consecutive_live_checks} checks)")
                    else:
                        logger.debug(f"  {status.platform_name}/{status.username}: Still offline ({status.consecutive_offline_checks} checks)")
            
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
