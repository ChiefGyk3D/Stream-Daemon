"""AI message generator supporting Google Gemini and Ollama."""

import os
import logging
import time
import threading
import re
from typing import Optional, List, Set
from ..config import get_config, get_bool_config, get_secret

# Import providers - may not be available if not configured
try:
    import google.genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global rate limiting: max 4 concurrent requests, 2-second minimum delay between calls
_api_semaphore = threading.Semaphore(4)
_last_api_call_time = 0
_api_call_lock = threading.Lock()
_min_delay_between_calls = 2.0  # seconds (30 requests/min = one every 2 seconds)


class AIMessageGenerator:
    """
    Generate personalized stream messages using AI (Google Gemini or Ollama).
    
    Features:
    - Support for multiple LLM providers (Gemini, Ollama)
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
        self.provider = None  # 'gemini' or 'ollama'
        self.api_key = None
        self.model = None
        self.client = None
        self.ollama_host = None
        self.ollama_client = None  # Separate Ollama client instance
        self.bluesky_max_chars = 300
        self.mastodon_max_chars = 500
        # Retry configuration for handling transient API errors (503, 429, etc.)
        self.max_retries = int(get_config('LLM', 'max_retries', default='3'))
        self.retry_delay_base = int(get_config('LLM', 'retry_delay_base', default='2'))
    
    @staticmethod
    def _tokenize_username(username: str) -> Set[str]:
        """
        Tokenize username into parts that should not appear in hashtags.
        
        Handles various username formats:
        - CamelCase: ChiefGyk3D -> ['chief', 'gyk', '3d', 'chiefgyk3d']
        - Underscores: Chief_Gyk3D -> ['chief', 'gyk', '3d', 'chief_gyk3d']
        - Numbers: Gamer123 -> ['gamer', '123', 'gamer123']
        - Prefixes: @username, #username -> removes prefix
        
        Args:
            username: The streamer's username
            
        Returns:
            Set of lowercase username parts (min 3 chars to avoid false positives)
        """
        if not username:
            return set()
        
        # Remove common prefixes (@, #)
        clean_username = username.lstrip('@#').strip()
        
        # Add the full username (lowercased) to the set
        parts = {clean_username.lower()}
        
        # Split on underscores, hyphens, dots
        for separator in ['_', '-', '.']:
            if separator in clean_username:
                parts.update(p.lower() for p in clean_username.split(separator) if len(p) >= 3)
        
        # Split CamelCase: ChiefGyk3D -> Chief, Gyk, 3D
        # Use regex to find transitions: lowercase->uppercase, letter->number, number->letter
        # Updated pattern to handle lowercase-before-uppercase (e.g., iPhone -> i, Phone)
        camel_parts = re.findall(r'[A-Z]*[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+', clean_username)
        parts.update(p.lower() for p in camel_parts if len(p) >= 3)
        
        # Also add consecutive parts for partial matches
        # Limit to up to 3 consecutive parts (e.g., for "ChiefGyk3D": Chief+Gyk, Gyk+3D, Chief+Gyk+3D)
        # This prevents O(n²) complexity while still catching most username variations
        for i in range(len(camel_parts)):
            for j in range(i + 1, min(i + 4, len(camel_parts) + 1)):  # i+1 to i+3 means up to 3 consecutive parts
                combined = ''.join(camel_parts[i:j]).lower()
                if len(combined) >= 3:
                    parts.add(combined)
        
        return parts
    
    @staticmethod
    def _extract_hashtags(message: str) -> List[str]:
        """
        Extract all hashtags from a message.
        
        Args:
            message: The generated message
            
        Returns:
            List of hashtags (without # prefix, lowercase)
        """
        # Match hashtags: # followed by alphanumeric characters
        hashtags = re.findall(r'#(\w+)', message)
        return [tag.lower() for tag in hashtags]
    
    @staticmethod
    def _remove_hashtag_from_message(message: str, hashtag: str) -> str:
        """
        Remove a specific hashtag from the message.
        
        Args:
            message: The message to modify
            hashtag: The hashtag to remove (without #)
            
        Returns:
            Message with the hashtag removed, cleaned up
        """
        # Remove the hashtag (case insensitive)
        pattern = r'#' + re.escape(hashtag) + r'\b'
        message = re.sub(pattern, '', message, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message
    
    @staticmethod
    def _validate_hashtags_against_username(message: str, username: str) -> str:
        """
        Remove hashtags that are derived from the username.
        
        This is a post-generation guardrail to filter out username-derived hashtags
        that the LLM may have incorrectly generated despite prompt instructions.
        
        Args:
            message: The generated message
            username: The streamer's username
            
        Returns:
            Message with username-derived hashtags removed
        """
        # Get username parts
        username_parts = AIMessageGenerator._tokenize_username(username)
        
        if not username_parts:
            return message
        
        # Extract hashtags from message
        hashtags = AIMessageGenerator._extract_hashtags(message)
        
        # Check each hashtag against username parts
        for hashtag in hashtags:
            # Check if hashtag matches or contains any username part
            should_remove = False
            
            # Direct match (exact match with any username part)
            if hashtag in username_parts:
                should_remove = True
                logger.debug(f"Removing hashtag #{hashtag} - direct match with username part")
            else:
                # Check if hashtag contains username parts (substring matching)
                # For 3-char parts, require exact match to avoid false positives
                # For 4+ char parts, allow substring matching for broader coverage
                for part in username_parts:
                    if len(part) >= 4 and part in hashtag:
                        should_remove = True
                        logger.debug(f"Removing hashtag #{hashtag} - contains username part '{part}'")
                        break
                    elif len(part) == 3 and part == hashtag:
                        # 3-char parts only match exactly (already handled by direct match above)
                        pass
            
            if should_remove:
                message = AIMessageGenerator._remove_hashtag_from_message(message, hashtag)
                logger.warning(f"⚠ Removed username-derived hashtag: #{hashtag}")
        
        return message
    
    @staticmethod
    def _safe_trim(message: str, limit: int) -> str:
        """
        Safely trim message to character limit without cutting words/hashtags mid-token.
        
        Args:
            message: The message to trim
            limit: Maximum character limit
        
        Returns:
            Trimmed message at word boundary, or hard cut if unavoidable
        """
        message = message.strip()
        if len(message) <= limit:
            return message
        
        # Try to trim at a word boundary to avoid cutting hashtags in half
        trimmed = message[:limit].rsplit(' ', 1)[0].rstrip()
        
        # If we trimmed too aggressively (e.g., single long token), hard cut
        return trimmed if trimmed else message[:limit]
    
    @staticmethod
    def _prompt_stream_start(platform_name: str, username: str, title: str, content_max: int) -> str:
        """
        Build optimized prompt for stream start messages.
        
        Designed for small LLMs (4B params) with explicit constraints to prevent hallucinations.
        
        Args:
            platform_name: Streaming platform (Twitch, YouTube, Kick)
            username: Streamer username
            title: Stream title
            content_max: Maximum character count for generated content
        
        Returns:
            Formatted prompt string
        """
        return f"""You write short go-live announcements for a streaming community.

Stream details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}

Hard rules:
- Output ONLY the post text (no quotes, no labels, no extra lines)
- MUST be <= {content_max} characters
- DO NOT include the URL (it will be appended automatically)
- DO NOT invent details not in the title (no giveaways, drops enabled, ranked grind, "new video", special guest, start times, or "tonight at X")
- Avoid cringe/clickbait words (smash that, unmissable, INSANE, crazy, epic, etc.)
- 1 emoji MAX (optional)

Style:
- Sound like a real person: short, punchy, slightly witty
- Include 1 clear call-to-action (e.g., "come hang out", "join me", "pull up")

Hashtags:
- Include EXACTLY 3 hashtags at the end (no more, no less)
- COUNT CAREFULLY: You must output exactly 3 hashtags, not 2, not 4, not 5
- Hashtags MUST be derived directly from words in the stream title only
- CRITICAL: DO NOT use the streamer's username "{username}" or ANY PART of it as a hashtag
- FORBIDDEN: Do not extract parts like words, numbers, or segments from "{username}" for hashtags
- DO NOT add generic tags like #Gaming, #Live, #Stream, #Community unless they appear in the title
- DO NOT add suffixes like #LiveStream or #TwitchLive
- If the title has no clear hashtag words, use: #{platform_name} #LiveStream #Community
- Format: Space before first hashtag, spaces between hashtags
- Example for "Minecraft Building": #Minecraft #Building #Creative (3 hashtags)
- Example for "Valorant Ranked": #Valorant #Ranked #Gaming (3 hashtags)

Now write the post."""
    
    @staticmethod
    def _prompt_stream_end(platform_name: str, username: str, title: str, prompt_max: int) -> str:
        """
        Build optimized prompt for stream end messages.
        
        Designed for small LLMs (4B params) with explicit constraints.
        
        Args:
            platform_name: Streaming platform (Twitch, YouTube, Kick)
            username: Streamer username  
            title: Stream title from when it started
            prompt_max: Maximum character count
        
        Returns:
            Formatted prompt string
        """
        return f"""You write short stream-ended thank-you posts for a streaming community.

Stream details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}

Hard rules:
- Output ONLY the post text (no quotes, no labels, no extra lines)
- MUST be <= {prompt_max} characters
- DO NOT invent details (no viewer counts, raid targets, highlights, "VOD coming soon", next stream times)
- Avoid cringe/clickbait words (amazing, incredible, INSANE, smashed it, etc.)
- 1 emoji MAX (optional)

Style:
- Sound genuine and grateful
- Keep it short and warm
- Simple thank you for joining

Hashtags:
- Include EXACTLY 2 hashtags at the end (no more, no less)
- COUNT CAREFULLY: You must output exactly 2 hashtags, not 1, not 3, not 4
- Hashtags MUST be derived directly from words in the stream title only
- CRITICAL: DO NOT use the streamer's username "{username}" or ANY PART of it as a hashtag
- FORBIDDEN: Do not extract parts like words, numbers, or segments from "{username}" for hashtags
- DO NOT add generic tags unless they appear in the title
- DO NOT add platform names unless necessary
- If the title has no clear hashtag words, use: #{platform_name} #GG
- Format: Space before first hashtag, space between hashtags
- Example for "Minecraft Building": #Minecraft #Building (2 hashtags)
- Example for "Valorant Ranked": #Valorant #Ranked (2 hashtags)

Now write the post."""
    
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
                    
                    # Make the API call based on provider
                    if self.provider == 'gemini':
                        response = self.client.models.generate_content(
                            model=self.model,
                            contents=prompt
                        )
                        return response.text.strip()
                    
                    elif self.provider == 'ollama':
                        response = self.ollama_client.chat(
                            model=self.model,
                            messages=[{'role': 'user', 'content': prompt}]
                        )
                        return response['message']['content'].strip()
                    
                    else:
                        logger.error(f"✗ Unknown provider: {self.provider}")
                        return None
                
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
        Initialize AI provider connection (Gemini or Ollama).
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not get_bool_config('LLM', 'enable', default=False):
                logger.info("LLM message generation disabled")
                return False
            
            # Determine which provider to use
            provider = get_config('LLM', 'provider', default='gemini').lower()
            self.provider = provider
            
            if provider == 'ollama':
                return self._authenticate_ollama()
            elif provider == 'gemini':
                return self._authenticate_gemini()
            else:
                logger.error(f"✗ Unknown LLM provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Failed to initialize LLM: {e}")
            self.enabled = False
            return False
    
    def _authenticate_ollama(self):
        """
        Initialize Ollama connection for local LLM.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not OLLAMA_AVAILABLE:
                logger.error("✗ Ollama Python client not installed. Run: pip install ollama")
                return False
            
            # Get Ollama configuration
            ollama_host = get_config('LLM', 'ollama_host', default='http://localhost')
            ollama_port = get_config('LLM', 'ollama_port', default='11434')
            model_name = get_config('LLM', 'model', default='gemma2:2b')
            
            # Build full host URL if port is specified separately
            if not ollama_host.startswith('http'):
                ollama_host = f"http://{ollama_host}"
            
            # Add port if not already in host URL
            if ':' not in ollama_host.split('//')[-1]:
                self.ollama_host = f"{ollama_host}:{ollama_port}"
            else:
                self.ollama_host = ollama_host
            
            self.model = model_name
            
            # Test connection by listing models
            try:
                self.ollama_client = ollama.Client(host=self.ollama_host)
                models_response = self.ollama_client.list()
                logger.debug(f"Connected to Ollama at {self.ollama_host}")
                
                # Check if requested model exists
                # Handle different response formats from ollama library
                available_models = []
                if hasattr(models_response, 'models'):
                    available_models = [m.get('name') or m.get('model') for m in models_response.models if m.get('name') or m.get('model')]
                elif isinstance(models_response, dict) and 'models' in models_response:
                    available_models = [m.get('name') or m.get('model') for m in models_response['models'] if m.get('name') or m.get('model')]
                
                if available_models and model_name not in available_models:
                    logger.warning(
                        f"⚠ Model '{model_name}' not found on Ollama server. "
                        f"Available models: {', '.join(available_models)}. "
                        f"To pull the model, run: ollama pull {model_name}"
                    )
                    # Don't fail - Ollama will auto-pull on first use
                
            except Exception as e:
                logger.error(f"✗ Failed to connect to Ollama at {self.ollama_host}: {e}")
                return False
            
            self.enabled = True
            logger.info(f"✓ Ollama LLM initialized (host: {self.ollama_host}, model: {model_name})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Ollama: {e}")
            return False
    
    def _authenticate_gemini(self):
        """
        Initialize Gemini API connection.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not GEMINI_AVAILABLE:
                logger.error("✗ Google Gemini client not installed. Run: pip install google-genai")
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
            
            # Build optimized prompt for small LLMs
            prompt = self._prompt_stream_start(platform_name, username, title, content_max)

            # Use retry logic for API call
            message = self._generate_with_retry(prompt)
            
            if message is None:
                # Retry failed
                return None
            
            # Verify content length (without URL yet) - use safe trimming to avoid cutting hashtags
            if len(message) > content_max:
                logger.warning(f"⚠ AI generated message too long ({len(message)} > {content_max}), trimming to fit")
                message = self._safe_trim(message, content_max)
            
            # Apply guardrail: Remove username-derived hashtags
            message = self._validate_hashtags_against_username(message, username)
            
            # Add URL to the message
            full_message = f"{message}\n\n{url}"
            
            # Final validation: ensure total length doesn't exceed limit
            if len(full_message) > max_chars:
                # This should rarely happen with our conservative limits, but handle it
                logger.warning(f"⚠ Final message exceeds {max_chars} chars ({len(full_message)}), trimming content")
                # Recalculate to fit exactly using safe trimming
                allowed_content = max_chars - url_formatting_space
                message = self._safe_trim(message, allowed_content)
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
            
            # Build optimized prompt for small LLMs
            prompt = self._prompt_stream_end(platform_name, username, title, prompt_max)

            # Use retry logic for API call
            message = self._generate_with_retry(prompt)
            
            if message is None:
                # Retry failed
                return None
            
            # Verify length - use safe trimming to avoid cutting hashtags mid-word
            if len(message) > max_chars:
                logger.warning(f"⚠ AI generated end message too long ({len(message)} > {max_chars}), trimming to fit")
                message = self._safe_trim(message, max_chars)
            
            # Apply guardrail: Remove username-derived hashtags
            message = self._validate_hashtags_against_username(message, username)
            
            logger.info(f"✨ Generated stream end message ({len(message)}/{max_chars} chars)")
            return message
            
        except Exception as e:
            logger.error(f"✗ Failed to generate end message: {e}")
            return None
