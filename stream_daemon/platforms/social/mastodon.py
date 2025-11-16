"""
Mastodon social platform implementation with threading support.
"""

import logging
from typing import Optional
from mastodon import Mastodon
from stream_daemon.config import get_config, get_bool_config, get_secret
from stream_daemon.config.constants import (
    SECRETS_AWS_MASTODON_SECRET_NAME,
    SECRETS_VAULT_MASTODON_SECRET_PATH,
    SECRETS_DOPPLER_MASTODON_SECRET_NAME
)

logger = logging.getLogger(__name__)


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
    """
    Mastodon social platform with threading support.
    
    Supports per-username configuration for multi-streamer monitoring.
    Each streamer can post to a different Mastodon instance/account.
    """
    
    def __init__(self):
        super().__init__("Mastodon")
        self.client = None  # Default client
        self.clients_per_user = {}  # "platform_username" -> Mastodon client instances
        
    def authenticate(self):
        if not get_bool_config('Mastodon', 'enable_posting', default=False):
            return False
            
        client_id = get_secret('Mastodon', 'client_id',
                              secret_name_env=SECRETS_AWS_MASTODON_SECRET_NAME,
                              secret_path_env=SECRETS_VAULT_MASTODON_SECRET_PATH,
                              doppler_secret_env=SECRETS_DOPPLER_MASTODON_SECRET_NAME)
        client_secret = get_secret('Mastodon', 'client_secret',
                                   secret_name_env=SECRETS_AWS_MASTODON_SECRET_NAME,
                                   secret_path_env=SECRETS_VAULT_MASTODON_SECRET_PATH,
                                   doppler_secret_env=SECRETS_DOPPLER_MASTODON_SECRET_NAME)
        access_token = get_secret('Mastodon', 'access_token',
                                  secret_name_env=SECRETS_AWS_MASTODON_SECRET_NAME,
                                  secret_path_env=SECRETS_VAULT_MASTODON_SECRET_PATH,
                                  doppler_secret_env=SECRETS_DOPPLER_MASTODON_SECRET_NAME)
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
            logger.info("✓ Mastodon authenticated (default account)")
            logger.info("  Per-username accounts supported (MASTODON_API_BASE_URL_PLATFORM_USERNAME)")
            return True
        except Exception as e:
            logger.warning(f"✗ Mastodon authentication failed: {e}")
            return False
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None, username: Optional[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        # Determine which client to use (per-username > default)
        client = None
        lookup_key = None
        
        if platform_name and username:
            # Try per-username configuration first
            lookup_key = f"{platform_name.lower()}_{username.lower()}"
            
            # Check if we've already loaded this user's client
            if lookup_key in self.clients_per_user:
                client = self.clients_per_user[lookup_key]
                logger.debug(f"Using cached per-user Mastodon client for {platform_name}/{username}")
            else:
                # Try to dynamically load per-username credentials
                # Build dynamic secret env names from base constants
                secret_suffix = f"_{lookup_key.upper()}_SECRET_NAME"
                aws_secret = f"{SECRETS_AWS_MASTODON_SECRET_NAME.replace('_SECRET_NAME', '')}{secret_suffix}"
                vault_secret = SECRETS_VAULT_MASTODON_SECRET_PATH.replace('_SECRET_PATH', f'_{lookup_key.upper()}_SECRET_PATH')
                doppler_secret = f"{SECRETS_DOPPLER_MASTODON_SECRET_NAME.replace('_SECRET_NAME', '')}{secret_suffix}"
                
                client_id = get_secret('Mastodon', f'client_id_{lookup_key}',
                                      secret_name_env=aws_secret,
                                      secret_path_env=vault_secret,
                                      doppler_secret_env=doppler_secret)
                client_secret = get_secret('Mastodon', f'client_secret_{lookup_key}',
                                          secret_name_env=aws_secret,
                                          secret_path_env=vault_secret,
                                          doppler_secret_env=doppler_secret)
                access_token = get_secret('Mastodon', f'access_token_{lookup_key}',
                                         secret_name_env=aws_secret,
                                         secret_path_env=vault_secret,
                                         doppler_secret_env=doppler_secret)
                api_base_url = get_config('Mastodon', f'api_base_url_{lookup_key}')
                
                if all([client_id, client_secret, access_token, api_base_url]):
                    try:
                        logger.info(f"Loading per-user Mastodon account for {platform_name}/{username}")
                        user_client = Mastodon(
                            client_id=client_id,
                            client_secret=client_secret,
                            access_token=access_token,
                            api_base_url=api_base_url
                        )
                        self.clients_per_user[lookup_key] = user_client
                        client = user_client
                        logger.info(f"✓ Per-user Mastodon authenticated for {platform_name}/{username}")
                    except Exception as auth_error:
                        logger.warning(f"⚠ Per-user Mastodon authentication failed for {platform_name}/{username}: {auth_error}")
                        logger.info(f"  Falling back to default Mastodon account")
        
        # Fallback to default client if no per-username client found
        if not client:
            client = self.client
            if not client:
                logger.error("✗ No Mastodon client available (neither per-user nor default)")
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
                                
                                media = client.media_post(tmp_path, description=description)
                                media_ids.append(media['id'])
                                logger.info(f"✓ Uploaded thumbnail to Mastodon (media ID: {media['id']})")
                            finally:
                                # Clean up temp file
                                os.unlink(tmp_path)
                    except Exception as img_error:
                        logger.warning(f"⚠ Could not upload thumbnail to Mastodon: {img_error}")
            
            # Post as a reply if reply_to_id is provided (threading)
            status = client.status_post(
                message, 
                in_reply_to_id=reply_to_id,
                media_ids=media_ids if media_ids else None
            )
            return str(status['id'])
        except Exception as e:
            logger.error(f"✗ Mastodon post failed: {e}")
            return None
