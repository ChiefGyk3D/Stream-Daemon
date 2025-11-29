"""Google Gemini AI message generator."""

import os
import logging
import time
import threading
import google.genai
from typing import Optional
from ..config import get_config, get_bool_config, get_secret

logger = logging.getLogger(__name__)

# Global rate limiting: max 4 concurrent requests, 2-second minimum delay between calls
_api_semaphore = threading.Semaphore(4)
_last_api_call_time = 0
_api_call_lock = threading.Lock()
_min_delay_between_calls = 2.0  # seconds (30 requests/min = one every 2 seconds)


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
    - Rate limiting: max 4 concurrent calls, 2-second delay between requests
    """
    
    def __init__(self):
        self.enabled = False
        self.api_key = None
        self.model = None
        self.client = None
        self.bluesky_max_chars = 300
        self.mastodon_max_chars = 500
        # Retry configuration for handling transient API errors (503, 429, etc.)
        self.max_retries = int(get_config('LLM', 'max_retries', default='3'))
        self.retry_delay_base = int(get_config('LLM', 'retry_delay_base', default='2'))
    
    def _generate_with_retry(self, prompt: str, max_retries: int = None) -> Optional[str]:
        """
        Generate content with exponential backoff retry logic.
        
        Handles transient errors like:
        - 503 Service Unavailable (model overloaded)
        - 429 Rate Limit Exceeded
        - Network timeouts
        
        Uses a global semaphore to limit concurrent API calls (max 4) and enforces
        minimum 2-second delay between requests to prevent quota exhaustion when
        multiple platforms go live simultaneously.
        
        Args:
            prompt: The prompt to send to the model
            max_retries: Maximum retry attempts (defaults to self.max_retries)
        
        Returns:
            Generated text or None if all retries fail
        """
        global _last_api_call_time
        
        if max_retries is None:
            max_retries = self.max_retries
        
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Rate limiting: wait for semaphore slot (max 4 concurrent)
                with _api_semaphore:
                    # Enforce minimum delay between API calls
                    with _api_call_lock:
                        time_since_last_call = time.time() - _last_api_call_time
                        if time_since_last_call < _min_delay_between_calls:
                            sleep_time = _min_delay_between_calls - time_since_last_call
                            logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s before API call")
                            time.sleep(sleep_time)
                        _last_api_call_time = time.time()
                    
                    # Make the API call
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt
                    )
                return response.text.strip()
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check if it's a retryable error
                is_retryable = (
                    '503' in error_str or  # Service Unavailable
                    '429' in error_str or  # Rate Limit
                    'overloaded' in error_str.lower() or
                    'quota' in error_str.lower() or
                    'timeout' in error_str.lower()
                )
                
                if not is_retryable or attempt >= max_retries:
                    # Non-retryable error or final attempt - give up
                    logger.error(f"✗ Failed to generate content: {e}")
                    return None
                
                # Calculate exponential backoff delay
                delay = self.retry_delay_base ** attempt
                logger.warning(
                    f"⚠ API error (attempt {attempt + 1}/{max_retries + 1}): {error_str}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
        
        # Should not reach here, but just in case
        logger.error(f"✗ Failed after {max_retries + 1} attempts: {last_error}")
        return None
        
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
            
            # Calculate exact space needed for URL and formatting
            # Format will be: "{message}\n\n{url}"
            # Reserve: 2 chars for "\n\n" + actual URL length
            url_formatting_space = len(url) + 2  # URL + two newlines
            
            # For Bluesky, cap content at 240 chars max to ensure room for URL + hashtags
            # This gives us: 240 (content) + 2 (newlines) + ~50 (typical URL) = ~292 chars
            # Leaves 8-char buffer for any URL length variations or formatting
            if social_platform.lower() == 'bluesky':
                # Hard cap content at 240 chars, regardless of URL length
                # This ensures we never exceed 300 even with long URLs and hashtags
                content_max = min(240, max_chars - url_formatting_space)
            else:
                # Other platforms are more forgiving
                content_max = max_chars - url_formatting_space
            
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

            # Use retry logic for API call
            message = self._generate_with_retry(prompt)
            
            if message is None:
                # Retry failed
                return None
            
            # Verify content length (without URL yet)
            if len(message) > content_max:
                logger.warning(f"⚠ AI generated message too long ({len(message)} > {content_max}), truncating to fit")
                message = message[:content_max]
            
            # Add URL to the message
            full_message = f"{message}\n\n{url}"
            
            # Final validation: ensure total length doesn't exceed limit
            if len(full_message) > max_chars:
                # This should rarely happen with our conservative limits, but handle it
                logger.warning(f"⚠ Final message exceeds {max_chars} chars ({len(full_message)}), truncating content")
                # Recalculate to fit exactly
                allowed_content = max_chars - url_formatting_space
                message = message[:allowed_content]
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
                # For Bluesky end messages, cap at 280 to leave room for hashtags
                # No URL in end messages, so we can be slightly less conservative
                prompt_max = 280
            elif social_platform.lower() == 'mastodon':
                max_chars = self.mastodon_max_chars
                prompt_max = max_chars
            else:
                max_chars = 500  # Default for Discord/Matrix
                prompt_max = max_chars
            
            prompt = f"""Generate a warm, thankful social media post announcing a livestream has ended.

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}

Requirements:
- Maximum {prompt_max} characters
- Thank viewers for joining
- Include 1-3 relevant hashtags based on the stream title
- Grateful and friendly tone
- Encourage them to catch the next stream
- Keep it concise and heartfelt

Generate ONLY the message text with hashtags, nothing else."""

            # Use retry logic for API call
            message = self._generate_with_retry(prompt)
            
            if message is None:
                # Retry failed
                return None
            
            # Verify length - truncate if needed
            if len(message) > max_chars:
                logger.warning(f"⚠ AI generated end message too long ({len(message)} > {max_chars}), truncating to fit")
                message = message[:max_chars]
            
            logger.info(f"✨ Generated stream end message ({len(message)}/{max_chars} chars)")
            return message
            
        except Exception as e:
            logger.error(f"✗ Failed to generate end message: {e}")
            return None
