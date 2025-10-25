"""Google Gemini AI message generator."""

import os
import logging
import google.genai
from typing import Optional
from ..config import get_config, get_bool_config, get_secret

logger = logging.getLogger(__name__)


class AIMessageGenerator:
    """
    Generate personalized stream messages using Google Gemini LLM.
    
    Features:
    - Platform-specific character limits (Bluesky: 300, Mastodon: 500)
    - Automatic hashtag generation based on stream title
    - Customizable tone for start vs. end messages
    - URL preservation
    - Fallback to standard messages if API fails
    - Error handling and retry logic
    """
    
    def __init__(self):
        self.enabled = False
        self.api_key = None
        self.model = None
        self.client = None
        self.bluesky_max_chars = 300
        self.mastodon_max_chars = 500
        
    def authenticate(self):
        """
        Initialize Gemini API connection.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not get_bool_config('LLM', 'enable', default=False):
                logger.info("LLM message generation disabled")
                return False
            
            # Get API key from secrets or env
            # Special case: GEMINI_API_KEY might be directly in Doppler/env, not prefixed with LLM_
            self.api_key = get_secret('LLM', 'gemini_api_key',
                                       secret_name_env='SECRETS_DOPPLER_LLM_SECRET_NAME',
                                       secret_path_env='SECRETS_VAULT_LLM_SECRET_PATH',
                                       doppler_secret_env='SECRETS_DOPPLER_LLM_SECRET_NAME')
            
            # Fallback: Check for GEMINI_API_KEY directly (common in Doppler)
            if not self.api_key:
                self.api_key = os.getenv('GEMINI_API_KEY')
            
            if not self.api_key:
                logger.error("✗ LLM enabled but no GEMINI_API_KEY found")
                return False
            
            # Configure Gemini with new google-genai package
            client = google.genai.Client(api_key=self.api_key)
            
            # Use gemini-2.0-flash-lite for high RPM (30/min), perfect for short social posts
            model_name = get_config('LLM', 'model', default='gemini-2.0-flash-lite')
            self.model = model_name
            self.client = client
            
            self.enabled = True
            logger.info(f"✓ Google Gemini LLM initialized (model: {model_name})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini: {e}")
            self.enabled = False
            return False
    
    def generate_stream_start_message(self, 
                                      platform_name: str,
                                      username: str, 
                                      title: str, 
                                      url: str,
                                      social_platform: str = "generic") -> Optional[str]:
        """
        Generate an engaging stream start message.
        
        Args:
            platform_name: Streaming platform (Twitch, YouTube, Kick)
            username: Streamer username
            title: Stream title
            url: Stream URL
            social_platform: Target social media (bluesky, mastodon, discord, matrix)
        
        Returns:
            Generated message or None if generation fails
        """
        if not self.enabled:
            return None
        
        try:
            # Determine character limit
            if social_platform.lower() == 'bluesky':
                max_chars = self.bluesky_max_chars
            elif social_platform.lower() == 'mastodon':
                max_chars = self.mastodon_max_chars
            else:
                max_chars = 500  # Default for Discord/Matrix
            
            # Reserve space for URL and spacing (more conservative to avoid truncation)
            # URL can be 30-50 chars + 2 newlines + safety margin
            url_space = len(url) + 20  # URL + newlines + safety buffer
            content_max = max_chars - url_space
            
            prompt = f"""Generate an exciting, engaging social media post announcing a livestream has just started.

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}
- URL: {url}

Requirements:
- Maximum {content_max} characters (excluding the URL which will be appended)
- Include 2-4 relevant hashtags based on the stream title
- Enthusiastic and inviting tone
- Make people want to join the stream NOW
- DO NOT include the URL in your response (it will be added automatically)
- Keep it concise and punchy

Generate ONLY the message text with hashtags, nothing else."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            message = response.text.strip()
            
            # Verify content length (without URL yet)
            if len(message) > content_max:
                # Truncate if AI generated too much
                message = message[:content_max-3] + "..."
            
            # Add URL to the message
            full_message = f"{message}\n\n{url}"
            
            logger.info(f"✨ Generated stream start message ({len(message)} chars content + URL = {len(full_message)}/{max_chars} total)")
            return full_message
            
        except Exception as e:
            logger.error(f"✗ Failed to generate start message: {e}")
            return None
    
    def generate_stream_end_message(self,
                                    platform_name: str,
                                    username: str,
                                    title: str,
                                    social_platform: str = "generic") -> Optional[str]:
        """
        Generate a thankful stream end message.
        
        Args:
            platform_name: Streaming platform (Twitch, YouTube, Kick)
            username: Streamer username  
            title: Stream title (from when it started)
            social_platform: Target social media (bluesky, mastodon, discord, matrix)
        
        Returns:
            Generated message or None if generation fails
        """
        if not self.enabled:
            return None
        
        try:
            # Determine character limit
            if social_platform.lower() == 'bluesky':
                max_chars = self.bluesky_max_chars
            elif social_platform.lower() == 'mastodon':
                max_chars = self.mastodon_max_chars
            else:
                max_chars = 500  # Default for Discord/Matrix
            
            prompt = f"""Generate a warm, thankful social media post announcing a livestream has ended.

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}

Requirements:
- Maximum {max_chars} characters
- Thank viewers for joining
- Include 1-3 relevant hashtags based on the stream title
- Grateful and friendly tone
- Encourage them to catch the next stream
- Keep it concise and heartfelt

Generate ONLY the message text with hashtags, nothing else."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            message = response.text.strip()
            
            # Verify length
            if len(message) > max_chars:
                message = message[:max_chars-3] + "..."
            
            logger.info(f"✨ Generated stream end message ({len(message)}/{max_chars} chars)")
            return message
            
        except Exception as e:
            logger.error(f"✗ Failed to generate end message: {e}")
            return None
