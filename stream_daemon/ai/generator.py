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
        # Generation parameters for better control with small LLMs
        # Temperature: Because even AI needs a chill pill to stop hallucinating
        # We set it low so the model doesn't get "creative" and start making shit up
        self.temperature = float(get_config('LLM', 'temperature', default='0.3'))
        self.top_p = float(get_config('LLM', 'top_p', default='0.9'))
        self.max_tokens = int(get_config('LLM', 'max_tokens', default='150'))
        
        # Guardrails configuration
        # Because we need rules to govern the rule-following machine. Meta as fuck.
        self.enable_deduplication = get_config('LLM', 'enable_deduplication', default='True').lower() == 'true'
        self.dedup_cache_size = int(get_config('LLM', 'dedup_cache_size', default='20'))
        self.enable_quality_scoring = get_config('LLM', 'enable_quality_scoring', default='False').lower() == 'true'
        self.min_quality_score = int(get_config('LLM', 'min_quality_score', default='6'))
        self.max_emoji_count = int(get_config('LLM', 'max_emoji_count', default='1'))
        self.enable_profanity_filter = get_config('LLM', 'enable_profanity_filter', default='False').lower() == 'true'
        self.profanity_severity = get_config('LLM', 'profanity_severity', default='moderate')
        self.enable_platform_validation = get_config('LLM', 'enable_platform_validation', default='True').lower() == 'true'
        
        # Deduplication cache: stores recent messages to prevent repeats
        # Because variety is the spice of life, even for robot-generated bullshit
        self._message_cache: List[str] = []
    
    @staticmethod
    def _tokenize_username(username: str) -> Set[str]:
        """
        Tokenize username into parts that should not appear in hashtags.
        
        Handles various username formats:
        - CamelCase: CoolStreamer99 -> ['cool', 'streamer', '99', 'coolstreamer99']
        - Underscores: Cool_Streamer_99 -> ['cool', 'streamer', 'cool_streamer_99']
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
        
        # Split CamelCase: CoolStreamer99 -> Cool, Streamer, 99
        # Use regex to find transitions: lowercase->uppercase, letter->number, number->letter
        # Updated pattern to handle lowercase-before-uppercase (e.g., iPhone -> i, Phone)
        camel_parts = re.findall(r'[A-Z]*[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+', clean_username)
        parts.update(p.lower() for p in camel_parts if len(p) >= 3)
        
        # Also add consecutive parts for partial matches
        # Limit to up to 3 consecutive parts (e.g., for "CoolStreamer99": Cool+Streamer, Streamer+99, Cool+Streamer+99)
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
        
        Because we need to teach a computer to recognize words that start with #.
        In the history of human civilization, this is where we ended up.
        
        Args:
            message: The generated message
            
        Returns:
            List of hashtags (without # prefix, lowercase)
        """
        # Match hashtags: # followed by a letter, then any alphanumeric characters
        # This excludes things like #50 (just numbers) which aren't valid hashtags
        hashtags = re.findall(r'#([a-zA-Z]\w*)', message)
        return [tag.lower() for tag in hashtags]
    
    @staticmethod
    def _contains_forbidden_words(message: str) -> tuple[bool, List[str]]:
        """
        Check if message contains clickbait/forbidden words that we explicitly told the AI not to use.
        
        This catches when the LLM ignores our prompt instructions.
        
        We built a machine that can process language at superhuman levels, and we use it
        to generate social media posts. Then we have to check if the machine used the words
        "INSANE" or "EPIC" because apparently we can't trust it to follow basic fucking instructions.
        
        It's like hiring a PhD to write greeting cards, then having to make sure they didn't
        write anything too smart. Welcome to the goddamn future.
        
        Args:
            message: The generated message
            
        Returns:
            tuple: (has_forbidden_words, list_of_found_words)
        """
        # Forbidden words we explicitly tell the AI not to use
        forbidden_words = [
            'insane', 'epic', 'crazy', 'smash', 'unmissable', 
            'incredible', 'amazing', 'lit', 'fire', 'legendary',
            'mind-blowing', 'jaw-dropping', 'unbelievable'
        ]
        
        message_lower = message.lower()
        found_words = []
        
        for word in forbidden_words:
            # Use word boundaries to avoid false positives (e.g., 'firewall' shouldn't match 'fire')
            if re.search(rf'\b{word}\b', message_lower):
                found_words.append(word)
        
        return (len(found_words) > 0, found_words)
    
    @staticmethod
    def _validate_message_quality(message: str, expected_hashtag_count: int, 
                                  title: str, username: str) -> tuple[bool, List[str]]:
        """
        Validate that generated message follows our rules.
        
        This is a post-generation quality check to catch when the LLM:
        - Uses wrong number of hashtags
        - Includes forbidden clickbait words
        - Accidentally includes the URL in content
        - Hallucinates details not in the title
        
        Yes, we have to fact-check the robot. The robot that we programmed. That we gave
        explicit instructions to. And it STILL fucks up about 10% of the time.
        
        It's like having a calculator that's right 90% of the time. Great job, humanity.
        We've achieved artificial intelligence that needs a fucking babysitter.
        
        George Carlin would lose his shit: "We can't trust people, so we built machines.
        Now we can't trust the machines either. What's next, we build machines to watch
        the machines? It's mistrust all the way down!"
        
        Args:
            message: The generated message (without URL)
            expected_hashtag_count: Expected number of hashtags (3 for start, 2 for end)
            title: Original stream title
            username: Streamer username
            
        Returns:
            tuple: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check hashtag count
        hashtags = AIMessageGenerator._extract_hashtags(message)
        if len(hashtags) != expected_hashtag_count:
            issues.append(f"Wrong hashtag count: {len(hashtags)} (expected {expected_hashtag_count})")
        
        # Check for forbidden words
        has_forbidden, found_words = AIMessageGenerator._contains_forbidden_words(message)
        if has_forbidden:
            issues.append(f"Contains forbidden words: {', '.join(found_words)}")
        
        # Check if message accidentally includes a URL (should be added separately)
        if re.search(r'https?://', message):
            issues.append("Message contains URL (should be added separately)")
        
        # Check for common hallucinations
        hallucination_patterns = [
            r'drops?\s+enabled',
            r'giveaway',
            r'tonight\s+at\s+\d',
            r'starting\s+at\s+\d',
            r'\d+\s*pm',
            r'\d+\s*am',
            r'vod\s+coming',
            r'vod\s+soon',
            r'next\s+stream',
            r'\d+\s+viewers?',
            r'raided?\s+',
            r'special\s+guest',
            r'new\s+video'
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                issues.append(f"Possible hallucination detected: '{pattern}'")
                break  # Only report first hallucination
        
        return (len(issues) == 0, issues)
    
    def _is_duplicate_message(self, message: str) -> bool:
        """
        Check if message is too similar to recent messages.
        
        Because nobody wants to read the same fucking announcement 5 times.
        Although to be fair, humans already do this manually. "Going live! Twitch!"
        "Going live! YouTube!" "Going live! Kick!" - Real creative there, chief.
        
        At least the AI has the decency to pretend it's trying to be different.
        
        Args:
            message: The generated message to check
            
        Returns:
            True if message is a duplicate or too similar
        """
        if not self.enable_deduplication:
            return False
        
        # Normalize message for comparison (lowercase, no emojis, no hashtags)
        normalized = message.lower()
        normalized = re.sub(r'#\w+', '', normalized)  # Remove hashtags
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation/emoji
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        
        # Check against cache
        for cached in self._message_cache:
            cached_normalized = cached.lower()
            cached_normalized = re.sub(r'#\w+', '', cached_normalized)
            cached_normalized = re.sub(r'[^\w\s]', '', cached_normalized)
            cached_normalized = re.sub(r'\s+', ' ', cached_normalized).strip()
            
            # If messages are >80% similar, consider it a duplicate
            if normalized == cached_normalized:
                return True
            
            # Calculate simple similarity (word overlap)
            msg_words = set(normalized.split())
            cached_words = set(cached_normalized.split())
            if len(msg_words) > 0 and len(cached_words) > 0:
                overlap = len(msg_words & cached_words) / max(len(msg_words), len(cached_words))
                if overlap > 0.8:
                    return True
        
        return False
    
    def _add_to_message_cache(self, message: str):
        """
        Add message to deduplication cache.
        
        Uses a simple FIFO queue. Old messages get pushed out.
        It's not rocket science, just a fucking list.
        
        Args:
            message: The message to cache
        """
        if not self.enable_deduplication:
            return
        
        self._message_cache.append(message)
        
        # Keep cache size limited
        if len(self._message_cache) > self.dedup_cache_size:
            self._message_cache.pop(0)
    
    @staticmethod
    def _count_emojis(message: str) -> int:
        """
        Count emoji characters in a message.
        
        Because apparently some people think more emojis = more engagement.
        Spoiler alert: It doesn't. You just look like you're 12.
        
        But hey, who am I to judge? I'm just here teaching robots not to spam emojis.
        Living the dream.
        
        Args:
            message: The message to check
            
        Returns:
            Number of emoji characters
        """
        # Unicode emoji ranges (basic coverage, not exhaustive)
        # Use proper character classes to avoid CodeQL warnings about overlapping ranges
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "]", flags=re.UNICODE
        )
        
        # Count individual emoji characters, not groups
        return len(emoji_pattern.findall(message))
    
    @staticmethod
    def _contains_profanity(message: str, severity: str = 'moderate') -> tuple[bool, List[str]]:
        """
        Check if message contains profanity.
        
        Ironic, considering this entire codebase is written by the ghost of George Carlin.
        But apparently we draw the line at the AI dropping F-bombs about Minecraft streams.
        
        "You can't say fuck on television!" - George Carlin, probably rolling in his grave
        that we're now censoring robots too.
        
        Args:
            message: The message to check
            severity: 'mild', 'moderate', or 'severe'
            
        Returns:
            tuple: (has_profanity, list_of_found_words)
        """
        # Profanity lists by severity (from mildest to most severe)
        mild_words = ['damn', 'hell', 'crap', 'suck', 'sucks', 'piss', 'pissed']
        moderate_words = ['ass', 'bastard', 'bitch', 'dick', 'cock', 'pussy', 'slut', 'whore']
        severe_words = ['fuck', 'fucking', 'shit', 'shitty', 'motherfucker', 'asshole', 'cunt']
        
        # Build word list based on severity
        # mild: only check mild words
        # moderate: check mild + moderate
        # severe: check all three levels
        if severity == 'severe':
            check_words = mild_words + moderate_words + severe_words
        elif severity == 'moderate':
            check_words = mild_words + moderate_words
        else:  # mild
            check_words = mild_words
        
        message_lower = message.lower()
        found_words = []
        
        for word in check_words:
            # Use word boundaries to avoid false positives (e.g., 'bass' shouldn't match 'ass')
            if re.search(rf'\b{word}\b', message_lower):
                found_words.append(word)
        
        return (len(found_words) > 0, found_words)
    
    @staticmethod
    def _score_message_quality(message: str, title: str) -> tuple[int, List[str]]:
        """
        Score message quality on a scale of 1-10.
        
        We're literally grading the AI's homework. Like it's in school.
        "Sorry robot, you get a C-. Try harder next time."
        
        This is what we've become. Quality control for artificial enthusiasm.
        George Carlin would have a 30-minute bit about this shit.
        
        Scoring criteria:
        - 10: Perfect (natural, engaging, unique)
        - 7-9: Good (clear, interesting)
        - 4-6: Mediocre (generic, boring)
        - 1-3: Bad (very generic, poor grammar, wrong info)
        
        Args:
            message: The generated message
            title: Original stream title
            
        Returns:
            tuple: (score 1-10, list_of_issues)
        """
        score = 10
        issues = []
        
        # Check for generic/overused phrases (deduct 2 points each)
        generic_phrases = [
            'come hang out',
            'let\'s go',
            'join me',
            'thanks for watching',
            'see you next time',
            'stream time',
            'going live'
        ]
        
        message_lower = message.lower()
        generic_count = sum(1 for phrase in generic_phrases if phrase in message_lower)
        if generic_count > 2:
            score -= 2
            issues.append(f"Too many generic phrases ({generic_count})")
        
        # Check length (too short = lazy, too long = rambling)
        content_without_hashtags = re.sub(r'#\w+', '', message).strip()
        word_count = len(content_without_hashtags.split())
        
        if word_count < 5:
            score -= 3
            issues.append("Too short (feels lazy)")
        elif word_count > 25:
            score -= 2
            issues.append("Too long (rambling)")
        
        # Check for repeated words (sign of poor generation)
        words = content_without_hashtags.lower().split()
        unique_ratio = len(set(words)) / len(words) if words else 0
        if unique_ratio < 0.7:  # >30% repeated words
            score -= 2
            issues.append("Too many repeated words")
        
        # Check for title integration (should reference stream content)
        title_words = set(title.lower().split())
        message_words = set(message_lower.split())
        overlap = len(title_words & message_words)
        
        if overlap == 0:
            score -= 3
            issues.append("Doesn't reference stream title/content")
        
        # Check if message is just reposting the title (should be based on it, not duplicate it)
        # Extract content before hashtags for comparison
        content_before_hashtags = re.split(r'\s+#', message)[0].strip()
        title_clean = title.strip()
        
        # Check if message is essentially just the title with minimal additions
        # Remove punctuation for better comparison
        content_no_punct = re.sub(r'[^\w\s]', '', content_before_hashtags.lower())
        title_no_punct = re.sub(r'[^\w\s]', '', title_clean.lower())
        
        # Case 1: Content is exactly the title (or title with punctuation)
        if content_no_punct.strip() == title_no_punct.strip():
            score -= 4
            issues.append("Message just reposts the title verbatim - should encourage engagement instead")
        # Case 2: Title makes up >70% of the content length (lazy repost with minor additions like "playing..." or "!")
        elif len(title_no_punct) > 0 and len(title_no_punct) / len(content_no_punct) > 0.7:
            score -= 3
            issues.append("Message too similar to title - should add value and encourage viewers")
        
        # Check for personality/engagement (exclamation marks, questions, emojis)
        has_personality = bool(
            re.search(r'[!?]', message) or
            re.search(r'[\U0001F600-\U0001F64F]', message)  # emoji
        )
        
        if not has_personality:
            score -= 1
            issues.append("Lacks personality (no punctuation variety or emoji)")
        
        # Clamp score to 1-10
        score = max(1, min(10, score))
        
        return (score, issues)
    
    def _validate_platform_specific(self, message: str, platform: str) -> List[str]:
        """
        Platform-specific validation rules.
        
        Because each social media platform is a special fucking snowflake
        with its own rules and quirks that we have to account for.
        
        Discord wants mentions and embeds formatted just so.
        Bluesky has its fancy "facets" and AT Protocol nonsense.
        Mastodon... well, Mastodon is pretty chill actually.
        
        But we still need to validate all this shit because apparently
        "just post some text" was too simple. Had to complicate it.
        
        Args:
            message: The generated message
            platform: Platform name (bluesky, mastodon, discord, matrix)
            
        Returns:
            list_of_issues (empty if valid)
        """
        if not self.enable_platform_validation:
            return []
        
        issues = []
        platform_lower = platform.lower()
        
        if platform_lower == 'discord':
            # Discord: Check for @everyone and @here (mass pings)
            if '@everyone' in message or '@here' in message:
                issues.append("Contains @everyone or @here mention")
            
            # Check for malformed mentions
            if re.search(r'@\d+>', message):
                issues.append("Malformed Discord mention detected")
            
            # Check for markdown that might break
            unmatched_markdown = (
                message.count('**') % 2 != 0 or
                message.count('__') % 2 != 0
            )
            if unmatched_markdown:
                issues.append("Unmatched markdown formatting")
        
        elif platform_lower == 'bluesky':
            # Bluesky: Check for issues that would break facets/link cards
            # Facets are their fancy word for "rich text annotations"
            
            # Check for URLs that aren't at the end (we add URL separately)
            urls_in_content = re.findall(r'https?://\S+', message)
            if urls_in_content:
                issues.append("URL found in content (should be added separately for facets)")
            
            # Check for @ mentions without handle format
            if '@' in message and not re.search(r'@[a-zA-Z0-9][a-zA-Z0-9-]*\.', message):
                issues.append("Malformed Bluesky handle (needs .domain)")
        
        elif platform_lower == 'mastodon':
            # Mastodon: Pretty forgiving, but check for HTML entities
            # and excessive formatting
            if re.search(r'&[a-z]+;', message):
                issues.append("HTML entities detected (should be plain text)")
        
        return issues
    
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
        
        Because apparently teaching a computer "don't use the person's name as a hashtag"
        is like explaining to your uncle why #MAGA isn't a personality trait.
        
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
    def _prompt_stream_start(platform_name: str, username: str, title: str, content_max: int, strict_mode: bool = False) -> str:
        """
        Build optimized prompt for stream start messages.
        
        Designed for small LLMs (4B params) with explicit constraints to prevent hallucinations.
        Uses step-by-step instructions and examples for better enforcement.
        
        Args:
            platform_name: Streaming platform (Twitch, YouTube, Kick)
            username: Streamer username
            title: Stream title
            content_max: Maximum character count for generated content
            strict_mode: If True, adds extra emphasis for rule compliance (used for retries)
        
        Returns:
            Formatted prompt string
        
        George Carlin would've loved this: We spent thousands of years teaching humans
        to write, and now we're teaching machines to sound like humans who can barely write.
        The irony is that we have to explicitly tell the AI NOT to sound like a fucking robot.
        "Don't say EPIC! Don't say INSANE!" - like we're training a puppy not to shit on the rug.
        """
        strict_prefix = ""
        if strict_mode:
            strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""
        
        return f"""{strict_prefix}You are a social media assistant that writes go-live stream announcements.

TASK: Write a short, engaging post announcing that {username} is live on {platform_name}.

STREAM TITLE: "{title}"

STEP 1 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {content_max} characters or less
✓ Output: ONLY the post text (no quotes, no meta-commentary, no labels)
✓ Tone: Casual, friendly, genuine (like a real person, not a bot)
✓ Call-to-action: Include ONE phrase like "come hang out", "join me", or "let's go"
✓ Emoji: Use 0-1 emoji maximum (optional)
✓ Based on title: Reference the stream topic BUT don't just copy/paste the title
✗ DO NOT just repost the title - the link already shows it, encourage people to watch instead
✗ DO NOT include the URL (it's added automatically)
✗ DO NOT invent details not in the title (no "drops enabled", "giveaways", "tonight at 7pm", etc.)
✗ DO NOT use cringe words: "INSANE", "EPIC", "smash that", "unmissable", "crazy"

STEP 2 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY 3 hashtags at the end.

Count: 1, 2, 3 hashtags. Not 2. Not 4. Exactly 3.
(Yes, we have to teach a computer how to count. Welcome to the future.)

Hashtag source rules:
- Extract hashtags ONLY from words in the stream title: "{title}"
- NEVER use the username "{username}" or any part of it as a hashtag
- NEVER use generic tags (#Gaming, #Live, #Stream) unless in the title
- Format: space before each hashtag

EXAMPLES:

Example 1:
Title: "Minecraft Creative Building"
Good post: "Building something cool in Minecraft! Come hang out and share ideas 🏗️ #Minecraft #Creative #Building"
(3 hashtags from title words)

Example 2:
Title: "Valorant Competitive"
Good post: "Ranked grind time! Let's climb together #Valorant #Competitive #FPS"
(3 hashtags, last one inferred from game type)

Example 3:
Title: "Just Chatting"
Good post: "Hanging out and talking about life. Join me! #JustChatting #{platform_name} #Community"
(Using platform when title is generic)

Bad examples to AVOID:
✗ "Epic stream starting NOW! #LIVE #INSANE #HYPE" (cringe words, generic tags)
✗ "Come watch! #TwitchStream #GamingLife" (generic, not from title)
✗ Using only 2 hashtags or using 4+ hashtags

NOW: Write the post for "{title}" on {platform_name}. Remember: exactly 3 hashtags, under {content_max} characters.

Post:"""
    
    @staticmethod
    def _prompt_stream_end(platform_name: str, username: str, title: str, prompt_max: int, strict_mode: bool = False) -> str:
        """
        Build optimized prompt for stream end messages.
        
        Designed for small LLMs (4B params) with explicit constraints.
        Uses step-by-step instructions and examples for better enforcement.
        
        Args:
            platform_name: Streaming platform (Twitch, YouTube, Kick)
            username: Streamer username  
            title: Stream title from when it started
            prompt_max: Maximum character count
            strict_mode: If True, adds extra emphasis for rule compliance (used for retries)
        
        Returns:
            Formatted prompt string
        """
        strict_prefix = ""
        if strict_mode:
            strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""
        
        return f"""{strict_prefix}You are a social media assistant that writes thank-you posts after streams end.

TASK: Write a short, grateful post thanking viewers for watching {username}'s stream.

STREAM TITLE: "{title}"

STEP 1 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {prompt_max} characters or less
✓ Output: ONLY the post text (no quotes, no meta-commentary)
✓ Tone: Warm, genuine, grateful (not overly enthusiastic)
✓ Message: Simple thank you for watching/joining
✓ Emoji: Use 0-1 emoji maximum (optional)
✓ Based on title: Reference what was streamed BUT don't just copy/paste the title
✗ DO NOT just repost the title - add gratitude and value instead
✗ DO NOT invent details (no "200 viewers", "raided someone", "highlight was X", "VOD soon")
✗ DO NOT mention next stream time or schedule
✗ DO NOT use exaggerated words: "AMAZING", "INCREDIBLE", "INSANE", "smashed it"

STEP 2 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY 2 hashtags at the end.

Count: 1, 2 hashtags. Not 1. Not 3. Exactly 2.

Hashtag source rules:
- Extract hashtags ONLY from words in the stream title: "{title}"
- NEVER use the username "{username}" or any part of it as a hashtag
- NEVER use generic tags unless the title has no clear words
- Format: space before each hashtag

EXAMPLES:

Example 1:
Title: "Minecraft Building"
Good post: "Thanks for hanging out while I built! See you next time 🏗️ #Minecraft #Building"
(2 hashtags from title)

Example 2:
Title: "Valorant Ranked"
Good post: "Stream's over! Thanks for watching the ranked grind gg #Valorant #Ranked"
(2 hashtags from title)

Example 3:
Title: "Just Chatting"
Good post: "Thanks for the great conversation today! #{platform_name} #GG"
(Using platform when title is generic)

Bad examples to AVOID:
✗ "AMAZING stream! 150 viewers! Raided someone! #EPIC #HYPE #GG" (invented details, 3 tags)
✗ "Thanks everyone! Stream again tomorrow at 7pm!" (mentioned next stream time)
✗ Using only 1 hashtag or using 3+ hashtags

NOW: Write the thank-you post for "{title}" on {platform_name}. Remember: exactly 2 hashtags, under {prompt_max} characters.

Post:"""
    
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
                        # Use generation config for better control with small models
                        config = {
                            'temperature': self.temperature,
                            'top_p': self.top_p,
                            'max_output_tokens': self.max_tokens,
                        }
                        response = self.client.models.generate_content(
                            model=self.model,
                            contents=prompt,
                            config=config
                        )
                        return response.text.strip()
                    
                    elif self.provider == 'ollama':
                        # Use generation options for better control
                        options = {
                            'temperature': self.temperature,
                            'top_p': self.top_p,
                            'num_predict': self.max_tokens,
                        }
                        response = self.ollama_client.chat(
                            model=self.model,
                            messages=[{'role': 'user', 'content': prompt}],
                            options=options
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
            
            # NEW GUARDRAILS: Additional quality checks (configurable via .env)
            all_issues = []
            
            # Check 1: Emoji count validation
            if self.max_emoji_count > 0:
                emoji_count = self._count_emojis(message)
                if emoji_count > self.max_emoji_count:
                    all_issues.append(f"Too many emojis: {emoji_count} (max: {self.max_emoji_count})")
            
            # Check 2: Profanity filter
            if self.enable_profanity_filter:
                has_profanity, profane_words = self._contains_profanity(message, self.profanity_severity)
                if has_profanity:
                    all_issues.append(f"Contains profanity: {', '.join(profane_words)}")
            
            # Check 3: Quality scoring
            if self.enable_quality_scoring:
                quality_score, quality_issues = self._score_message_quality(message, title)
                if quality_score < self.min_quality_score:
                    all_issues.append(f"Quality score too low: {quality_score}/10 (min: {self.min_quality_score})")
                    all_issues.extend(quality_issues)
            
            # Check 4: Platform-specific validation
            platform_issues = self._validate_platform_specific(message, social_platform)
            if len(platform_issues) > 0:
                all_issues.extend(platform_issues)
            
            # Check 5: Deduplication check
            if self._is_duplicate_message(message):
                all_issues.append("Message too similar to recent announcements")
            
            # Post-generation quality check (original hashtag/forbidden word validation)
            is_valid, issues = self._validate_message_quality(message, 3, title, username)
            if not is_valid:
                all_issues.extend(issues)
            
            # If ANY guardrail failed, retry once with strict mode
            if len(all_issues) > 0:
                logger.warning(f"⚠ Generated message has {len(all_issues)} issue(s): {', '.join(all_issues[:3])}{'...' if len(all_issues) > 3 else ''}")
                # Try ONE more time with stricter instructions
                logger.info("🔄 Retrying with stricter prompt...")
                strict_prompt = self._prompt_stream_start(platform_name, username, title, content_max, strict_mode=True)
                retry_message = self._generate_with_retry(strict_prompt)
                
                if retry_message:
                    # Re-validate ALL guardrails on retry
                    retry_issues = []
                    
                    # Trim and clean retry
                    if len(retry_message) > content_max:
                        retry_message = self._safe_trim(retry_message, content_max)
                    retry_message = self._validate_hashtags_against_username(retry_message, username)
                    
                    # Check all guardrails again
                    if self.max_emoji_count > 0 and self._count_emojis(retry_message) > self.max_emoji_count:
                        retry_issues.append("emojis")
                    if self.enable_profanity_filter and self._contains_profanity(retry_message, self.profanity_severity)[0]:
                        retry_issues.append("profanity")
                    if self.enable_quality_scoring:
                        retry_score, _ = self._score_message_quality(retry_message, title)
                        if retry_score < self.min_quality_score:
                            retry_issues.append(f"quality({retry_score}/10)")
                    platform_retry_issues = self._validate_platform_specific(retry_message, social_platform)
                    if len(platform_retry_issues) > 0:
                        retry_issues.append("platform")
                    if self._is_duplicate_message(retry_message):
                        retry_issues.append("duplicate")
                    retry_valid, _ = self._validate_message_quality(retry_message, 3, title, username)
                    if not retry_valid:
                        retry_issues.append("hashtags/forbidden")
                    
                    if len(retry_issues) == 0:
                        logger.info("✅ Retry produced valid message, using it")
                        message = retry_message
                    else:
                        logger.warning(f"⚠ Retry still has issues: {', '.join(retry_issues)}, using original")
                        # Keep original message - it's better to have minor issues than fail completely
                else:
                    logger.warning("⚠ Retry failed, using original message despite issues")
            
            # Add to deduplication cache (after all validation/retries)
            self._add_to_message_cache(message)
            
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
            
            # NEW GUARDRAILS: Additional quality checks (configurable via .env)
            all_issues = []
            
            # Check 1: Emoji count validation
            if self.max_emoji_count > 0:
                emoji_count = self._count_emojis(message)
                if emoji_count > self.max_emoji_count:
                    all_issues.append(f"Too many emojis: {emoji_count} (max: {self.max_emoji_count})")
            
            # Check 2: Profanity filter
            if self.enable_profanity_filter:
                has_profanity, profane_words = self._contains_profanity(message, self.profanity_severity)
                if has_profanity:
                    all_issues.append(f"Contains profanity: {', '.join(profane_words)}")
            
            # Check 3: Quality scoring
            if self.enable_quality_scoring:
                quality_score, quality_issues = self._score_message_quality(message, title)
                if quality_score < self.min_quality_score:
                    all_issues.append(f"Quality score too low: {quality_score}/10 (min: {self.min_quality_score})")
                    all_issues.extend(quality_issues)
            
            # Check 4: Platform-specific validation
            platform_issues = self._validate_platform_specific(message, social_platform)
            if len(platform_issues) > 0:
                all_issues.extend(platform_issues)
            
            # Check 5: Deduplication check
            if self._is_duplicate_message(message):
                all_issues.append("Message too similar to recent announcements")
            
            # Post-generation quality check (expect 2 hashtags for end messages)
            is_valid, issues = self._validate_message_quality(message, 2, title, username)
            if not is_valid:
                all_issues.extend(issues)
            
            # If ANY guardrail failed, retry once with strict mode
            if len(all_issues) > 0:
                logger.warning(f"⚠ Generated end message has {len(all_issues)} issue(s): {', '.join(all_issues[:3])}{'...' if len(all_issues) > 3 else ''}")
                # Try ONE more time with stricter instructions
                logger.info("🔄 Retrying with stricter prompt...")
                strict_prompt = self._prompt_stream_end(platform_name, username, title, prompt_max, strict_mode=True)
                retry_message = self._generate_with_retry(strict_prompt)
                
                if retry_message:
                    # Re-validate ALL guardrails on retry
                    retry_issues = []
                    
                    # Trim and clean retry
                    if len(retry_message) > max_chars:
                        retry_message = self._safe_trim(retry_message, max_chars)
                    retry_message = self._validate_hashtags_against_username(retry_message, username)
                    
                    # Check all guardrails again
                    if self.max_emoji_count > 0 and self._count_emojis(retry_message) > self.max_emoji_count:
                        retry_issues.append("emojis")
                    if self.enable_profanity_filter and self._contains_profanity(retry_message, self.profanity_severity)[0]:
                        retry_issues.append("profanity")
                    if self.enable_quality_scoring:
                        retry_score, _ = self._score_message_quality(retry_message, title)
                        if retry_score < self.min_quality_score:
                            retry_issues.append(f"quality({retry_score}/10)")
                    platform_retry_issues = self._validate_platform_specific(retry_message, social_platform)
                    if len(platform_retry_issues) > 0:
                        retry_issues.append("platform")
                    if self._is_duplicate_message(retry_message):
                        retry_issues.append("duplicate")
                    retry_valid, _ = self._validate_message_quality(retry_message, 2, title, username)
                    if not retry_valid:
                        retry_issues.append("hashtags/forbidden")
                    
                    if len(retry_issues) == 0:
                        logger.info("✅ Retry produced valid message, using it")
                        message = retry_message
                    else:
                        logger.warning(f"⚠ Retry still has issues: {', '.join(retry_issues)}, using original")
                        # Keep original - better to have minor issues than fail completely
                else:
                    logger.warning("⚠ Retry failed, using original message despite issues")
            
            # Add to deduplication cache (after all validation/retries)
            self._add_to_message_cache(message)
            
            logger.info(f"✨ Generated stream end message ({len(message)}/{max_chars} chars)")
            return message
            
        except Exception as e:
            logger.error(f"✗ Failed to generate end message: {e}")
            return None
