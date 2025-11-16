"""
Threads (Meta) social platform implementation with threading support.

Threads API Documentation: https://developers.facebook.com/docs/threads/
"""

import logging
import time
from typing import Optional
import requests
from stream_daemon.config import get_config, get_bool_config, get_secret

logger = logging.getLogger(__name__)


class ThreadsPlatform:
    """Threads (Meta) social platform with threading support."""
    
    def __init__(self):
        self.name = "Threads"
        self.enabled = False
        self.user_id = None
        self.access_token = None
        self.base_url = "https://graph.threads.net/v1.0"
        
    def authenticate(self):
        """Authenticate with Threads API using Instagram-based access token."""
        if not get_bool_config('Threads', 'enable_posting', default=False):
            return False
            
        self.user_id = get_config('Threads', 'user_id')
        self.access_token = get_secret('Threads', 'access_token',
                                       secret_name_env='SECRETS_AWS_THREADS_SECRET_NAME',
                                       secret_path_env='SECRETS_VAULT_THREADS_SECRET_PATH',
                                       doppler_secret_env='SECRETS_DOPPLER_THREADS_SECRET_NAME')
        
        if not all([self.user_id, self.access_token]):
            logger.warning("✗ Threads authentication failed: missing user_id or access_token")
            return False
            
        # Test authentication by fetching user profile
        try:
            test_url = f"{self.base_url}/{self.user_id}"
            params = {
                'fields': 'id,username',
                'access_token': self.access_token
            }
            response = requests.get(test_url, params=params, timeout=10)
            response.raise_for_status()
            
            profile_data = response.json()
            username = profile_data.get('username', 'unknown')
            
            self.enabled = True
            logger.info(f"✓ Threads authenticated (@{username})")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"✗ Threads authentication failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.warning(f"   API Error: {error_data}")
                except Exception:
                    logger.warning(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            logger.warning(f"✗ Threads authentication failed: {e}")
            return False
    
    def _create_media_container(self, message: str, reply_to_id: Optional[str] = None) -> Optional[str]:
        """
        Step 1: Create a Threads media container.
        
        Args:
            message: The message text (max 500 chars)
            reply_to_id: Optional post ID to reply to (for threading)
            
        Returns:
            Container ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{self.user_id}/threads"
            
            # Threads has a 500 character limit
            if len(message) > 500:
                logger.error(f"✗ CRITICAL: Message exceeds Threads' 500 char limit ({len(message)} chars)")
                logger.error(f"   This should not happen - check AI generator logic!")
                # Emergency truncate as last resort
                message = message[:500]
                logger.warning(f"   Emergency truncated to 500 chars")
            
            params = {
                'media_type': 'TEXT',
                'text': message,
                'access_token': self.access_token
            }
            
            # Add reply_to parameter if this is a reply/thread
            if reply_to_id:
                params['reply_to_id'] = reply_to_id
            
            response = requests.post(url, data=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            container_id = data.get('id')
            
            if container_id:
                logger.debug(f"ℹ Threads container created: {container_id}")
                return container_id
            else:
                logger.error(f"✗ Threads container creation failed: no ID in response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Threads container creation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"   API Error: {error_data}")
                except Exception:
                    logger.error(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"✗ Threads container creation failed: {e}")
            return None
    
    def _publish_media_container(self, container_id: str) -> Optional[str]:
        """
        Step 2: Publish the Threads media container.
        
        Args:
            container_id: The container ID from step 1
            
        Returns:
            Post ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{self.user_id}/threads_publish"
            
            params = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            post_id = data.get('id')
            
            if post_id:
                logger.debug(f"ℹ Threads post published: {post_id}")
                return post_id
            else:
                logger.error(f"✗ Threads publish failed: no ID in response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Threads publish failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"   API Error: {error_data}")
                except Exception:
                    logger.error(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"✗ Threads publish failed: {e}")
            return None
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        """
        Post message to Threads using the two-step process.
        
        Args:
            message: The message to post (max 500 chars)
            reply_to_id: Optional post ID to reply to (for threading)
            platform_name: Optional streaming platform name (not used by Threads)
            stream_data: Optional stream metadata (not used for basic text posts)
            
        Returns:
            Post ID if successful, None otherwise
        """
        if not self.enabled:
            logger.debug("ℹ Threads posting disabled")
            return None
            
        try:
            # Step 1: Create media container
            container_id = self._create_media_container(message, reply_to_id)
            if not container_id:
                return None
            
            # Step 2: Wait recommended time before publishing (30 seconds recommended by API docs)
            # For text-only posts this is usually not necessary, but we'll wait briefly to be safe
            time.sleep(2)  # Wait 2 seconds for text posts (30s is for media processing)
            
            # Step 3: Publish the container
            post_id = self._publish_media_container(container_id)
            
            if post_id:
                if reply_to_id:
                    logger.info(f"✓ Threads reply posted: {post_id}")
                else:
                    logger.info(f"✓ Threads post published: {post_id}")
                return post_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"✗ Threads post failed: {e}")
            return None
