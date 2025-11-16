"""Twitch streaming platform integration."""

import logging
import asyncio
from typing import Optional, Tuple

from twitchAPI.twitch import Twitch

from stream_daemon.config import get_secret
from stream_daemon.config.constants import (
    SECRETS_AWS_TWITCH_SECRET_NAME,
    SECRETS_VAULT_TWITCH_SECRET_PATH,
    SECRETS_DOPPLER_TWITCH_SECRET_NAME
)
from stream_daemon.platforms.base import StreamingPlatform

logger = logging.getLogger(__name__)


class TwitchPlatform(StreamingPlatform):
    """Twitch streaming platform with enhanced error handling and retry logic."""
    
    def __init__(self):
        super().__init__("Twitch")
        self.client = None
        self.client_id = None
        self.client_secret = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
    def authenticate(self) -> bool:
        """Authenticate with Twitch API with error handling."""
        try:
            self.client_id = get_secret('Twitch', 'client_id', 
                                  secret_name_env=SECRETS_AWS_TWITCH_SECRET_NAME,
                                  secret_path_env=SECRETS_VAULT_TWITCH_SECRET_PATH,
                                  doppler_secret_env=SECRETS_DOPPLER_TWITCH_SECRET_NAME)
            self.client_secret = get_secret('Twitch', 'client_secret',
                                       secret_name_env=SECRETS_AWS_TWITCH_SECRET_NAME,
                                       secret_path_env=SECRETS_VAULT_TWITCH_SECRET_PATH,
                                       doppler_secret_env=SECRETS_DOPPLER_TWITCH_SECRET_NAME)
            
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
    
    def is_live(self, username: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if Twitch stream is live with retry logic and error handling.
        
        Args:
            username: Twitch username to check
            
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
