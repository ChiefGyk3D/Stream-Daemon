# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AI message generation for stream announcements, built on hypeman-social.

Provider plumbing (Ollama, Gemini, retries, reconnection, thinking-mode
extraction, failover) lives in the shared library now. What stays here is
stream-daemon's own voice: go-live and thanks-for-watching prompts, per-network
character budgets, and the lenient validate-retry-keep flow — a stream
announcement with a minor style issue still beats posting nothing.

Same configuration as always (LLM_ENABLE, LLM_PROVIDER, LLM_OLLAMA_HOST,
LLM_MAX_EMOJI_COUNT, ...), plus LLM_FALLBACK_PROVIDER for automatic failover.
"""

import logging

from hypeman_social.llm import STREAM_PROFILE, LLMManager
from hypeman_social.llm import guardrails as _guardrails

from stream_daemon.config import get_bool_config, get_config, get_secret

# Availability flags for the optional provider SDKs, re-exported from the
# library for callers (and test patches) that consult them here.
try:
    from hypeman_social.llm.ollama import OLLAMA_AVAILABLE
except ImportError:  # pragma: no cover
    OLLAMA_AVAILABLE = False
try:
    from hypeman_social.llm.gemini import GEMINI_AVAILABLE
except ImportError:  # pragma: no cover
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

# get_secret and the availability flags are part of this module's public
# surface (tests patch them here; callers historically read them here).
__all__ = [
    'GEMINI_AVAILABLE',
    'OLLAMA_AVAILABLE',
    'AIMessageGenerator',
    'get_bool_config',
    'get_config',
    'get_secret',
]


class AIMessageGenerator:
    """
    Generate personalized stream messages using AI (Ollama or Gemini).

    Wraps hypeman-social's LLMManager: automatic reconnection when a local
    Ollama box comes back, and opt-in failover via LLM_FALLBACK_PROVIDER.
    The daemon-facing interface is unchanged from the pre-library version.
    """

    def __init__(self):
        self.engine = LLMManager(profile=STREAM_PROFILE)
        self.enabled = False
        self.provider: str | None = None
        self.model: str | None = None

        self.bluesky_max_chars = 300
        self.mastodon_max_chars = 500

        # Guardrail configuration — same env keys the library providers read,
        # held here too because the lenient flow below applies them itself.
        self.max_emoji_count = int(get_config('LLM', 'max_emoji_count', default='2'))
        self.enable_profanity_filter = get_bool_config(
            'LLM', 'enable_profanity_filter', default=False)
        self.profanity_severity = get_config('LLM', 'profanity_severity', default='moderate')
        self.enable_quality_scoring = get_bool_config(
            'LLM', 'enable_quality_scoring', default=False)
        self.min_quality_score = int(get_config('LLM', 'min_quality_score', default='6'))

        # Generation parameters, mirrored from the library's config keys for
        # callers that read them off the generator.
        self.max_tokens = int(get_config('LLM', 'max_tokens', default='150'))
        self.max_retries = int(get_config('LLM', 'max_retries', default='3'))
        self.retry_delay_base = float(get_config('LLM', 'retry_delay_base', default='2'))
        self.enable_thinking_mode = get_bool_config('LLM', 'enable_thinking_mode', default=False)
        self.thinking_token_multiplier = float(
            get_config('LLM', 'thinking_token_multiplier', default='4.0'))

    # Deduplication state lives on the manager so a provider failover doesn't
    # wipe it; these properties keep the generator's historical surface.

    @property
    def enable_deduplication(self) -> bool:
        return self.engine.enable_deduplication

    @enable_deduplication.setter
    def enable_deduplication(self, value: bool) -> None:
        self.engine.enable_deduplication = value

    @property
    def dedup_cache_size(self) -> int:
        return self.engine.dedup_cache_size

    @dedup_cache_size.setter
    def dedup_cache_size(self, value: int) -> None:
        self.engine.dedup_cache_size = value

    @property
    def _message_cache(self):
        return self.engine._message_cache

    @_message_cache.setter
    def _message_cache(self, value) -> None:
        self.engine._message_cache = value

    def authenticate(self) -> bool:
        """
        Bring up the configured provider(s).

        Unlike the old implementation, a provider that is down at startup is
        not fatal: it stays configured and recovers when the server returns.
        """
        if not self.engine.authenticate():
            self.enabled = False
            return False

        self.enabled = True
        self.provider = self.engine.provider
        active = self.engine.active or self.engine.primary
        self.model = getattr(active, 'model', None)
        return True

    def is_available(self) -> bool:
        """True if any provider can generate right now. May heal a downed one."""
        return self.engine.is_available()

    def status(self) -> dict:
        """Provider state for logs and health endpoints."""
        return self.engine.status()

    # ─────────────────────────────────────────────────────────────────────
    # Message generation
    # ─────────────────────────────────────────────────────────────────────

    def generate_stream_start_message(self,
                                      platform_name: str,
                                      username: str,
                                      title: str,
                                      url: str,
                                      social_platform: str = "generic") -> str | None:
        """
        Generate an engaging stream start message, URL appended.

        Returns None when generation fails outright; the caller falls back to
        its template messages.
        """
        if not self.enabled:
            return None

        try:
            if social_platform.lower() == 'bluesky':
                max_chars = self.bluesky_max_chars
            elif social_platform.lower() == 'mastodon':
                max_chars = self.mastodon_max_chars
            else:
                max_chars = 500  # Default for Discord/Matrix

            # Reserve room for "\n\n{url}". Bluesky content is hard-capped at
            # 240 so a long URL plus hashtags can never push past 300.
            url_formatting_space = len(url) + 2
            if social_platform.lower() == 'bluesky':
                content_max = min(240, max_chars - url_formatting_space)
            else:
                content_max = max_chars - url_formatting_space

            message = self._generate_validated(
                lambda strict: self._prompt_stream_start(
                    platform_name, username, title, content_max, strict_mode=strict),
                title=title,
                username=username,
                social_platform=social_platform,
                content_max=content_max,
                expected_hashtags=3,
            )
            if message is None:
                return None

            full_message = f"{message}\n\n{url}"

            # Final safety: never exceed the platform limit even with an
            # unusually long URL.
            if len(full_message) > max_chars:
                logger.warning(
                    f"⚠ Final message exceeds {max_chars} chars ({len(full_message)}), trimming content")
                message = self._safe_trim(message, max_chars - url_formatting_space)
                full_message = f"{message}\n\n{url}"

            logger.info(
                f"✨ Generated stream start message "
                f"({len(message)} chars content + URL = {len(full_message)}/{max_chars} total)")
            return full_message

        except Exception as e:  # noqa: BLE001  # fall back to a template message; error is logged
            logger.error(f"✗ Failed to generate start message: {e}")
            return None

    def generate_stream_end_message(self,
                                    platform_name: str,
                                    username: str,
                                    title: str | None = None,
                                    social_platform: str = "generic") -> str | None:
        """Generate a thankful stream end message (no URL)."""
        if not self.enabled:
            return None

        # Stream state clears the title when a channel goes offline.
        if title is None:
            title = 'Stream'

        try:
            if social_platform.lower() == 'bluesky':
                max_chars = self.bluesky_max_chars
                prompt_max = 280  # leave room for hashtags
            elif social_platform.lower() == 'mastodon':
                max_chars = self.mastodon_max_chars
                prompt_max = max_chars
            else:
                max_chars = 500
                prompt_max = max_chars

            message = self._generate_validated(
                lambda strict: self._prompt_stream_end(
                    platform_name, username, title, prompt_max, strict_mode=strict),
                title=title,
                username=username,
                social_platform=social_platform,
                content_max=max_chars,
                expected_hashtags=2,
            )
            if message is None:
                return None

            logger.info(f"✨ Generated stream end message ({len(message)}/{max_chars} chars)")
            return message

        except Exception as e:  # noqa: BLE001  # fall back to a template message; error is logged
            logger.error(f"✗ Failed to generate end message: {e}")
            return None

    def _generate_validated(self, build_prompt, title: str, username: str,
                            social_platform: str, content_max: int,
                            expected_hashtags: int) -> str | None:
        """
        Generate, validate, and retry once with a stricter prompt on issues.

        Deliberately lenient: when the strict retry still has issues, the
        original message ships anyway (minor style problems beat silence) —
        with one exception: profanity when the filter is on.
        """
        message = self._generate_with_retry(build_prompt(False))
        if message is None:
            return None

        message = self._clean(message, content_max, username)
        issues = self._check_guardrails(
            message, title, username, social_platform, expected_hashtags)

        if issues:
            preview = ', '.join(issues[:3]) + ('...' if len(issues) > 3 else '')
            logger.warning(f"⚠ Generated message has {len(issues)} issue(s): {preview}")
            logger.info("🔄 Retrying with stricter prompt...")

            retry_message = self._generate_with_retry(build_prompt(True))
            if retry_message:
                retry_message = self._clean(retry_message, content_max, username)
                retry_issues = self._check_guardrails(
                    retry_message, title, username, social_platform, expected_hashtags)
                if not retry_issues:
                    logger.info("✅ Retry produced valid message, using it")
                    message = retry_message
                    issues = []
                else:
                    logger.warning(
                        f"⚠ Retry still has issues: {', '.join(retry_issues[:3])}, using original")
            else:
                logger.warning("⚠ Retry failed, using original message despite issues")

        # The one hard veto: profanity with the filter enabled.
        if issues and self.enable_profanity_filter:
            has_profanity, found = self._contains_profanity(message, self.profanity_severity)
            if has_profanity:
                logger.warning(f"✗ Dropping message, contains profanity: {', '.join(found)}")
                return None

        self._add_to_message_cache(message)
        return message

    def _clean(self, message: str, content_max: int, username: str) -> str:
        """Trim to budget and strip username-derived hashtags."""
        if len(message) > content_max:
            logger.warning(
                f"⚠ AI generated message too long ({len(message)} > {content_max}), trimming to fit")
            message = self._safe_trim(message, content_max)
        return self._validate_hashtags_against_username(message, username)

    def _check_guardrails(self, message: str, title: str, username: str,
                          social_platform: str, expected_hashtags: int) -> list[str]:
        """Every configured quality check; returns the list of issues found."""
        issues: list[str] = []

        if self.max_emoji_count > 0:
            emoji_count = self._count_emojis(message)
            if emoji_count > self.max_emoji_count:
                issues.append(f"Too many emojis: {emoji_count} (max: {self.max_emoji_count})")

        if self.enable_profanity_filter:
            has_profanity, profane_words = self._contains_profanity(
                message, self.profanity_severity)
            if has_profanity:
                issues.append(f"Contains profanity: {', '.join(profane_words)}")

        if self.enable_quality_scoring:
            quality_score, quality_issues = self._score_message_quality(message, title)
            if quality_score < self.min_quality_score:
                issues.append(
                    f"Quality score too low: {quality_score}/10 (min: {self.min_quality_score})")
                issues.extend(quality_issues)

        issues.extend(self._validate_platform_specific(message, social_platform))

        if self._is_duplicate_message(message):
            issues.append("Message too similar to recent announcements")

        is_valid, quality_issues = self._validate_message_quality(
            message, expected_hashtags, title, username)
        if not is_valid:
            issues.extend(quality_issues)

        return issues

    def _generate_with_retry(self, prompt: str, max_retries: int | None = None) -> str | None:
        """
        One generation through the manager.

        Retries, backoff, reconnection, and provider failover all happen
        inside hypeman-social; this wrapper exists for interface stability.
        """
        return self.engine.generate(prompt)

    # ─────────────────────────────────────────────────────────────────────
    # Prompts
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _prompt_stream_start(platform_name: str, username: str, title: str,
                             content_max: int, strict_mode: bool = False) -> str:
        """
        Build optimized prompt for stream start messages.

        Designed for small LLMs (4B params) with explicit constraints to
        prevent hallucinations; step-by-step instructions and examples.
        """
        strict_prefix = ""
        if strict_mode:
            strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""

        return f"""{strict_prefix}You are a social media assistant that writes go-live stream announcements with personality and hype.

TASK: Write a short, engaging post announcing that {username} is live on {platform_name}.

STREAM TITLE: "{title}"

STEP 1 - STYLE & TONE:
✓ Match the vibe: Read the title and match its energy (technical/professional, gaming/competitive, casual/chill, creative/artistic, etc.)
✓ Be personality-driven: Write like a real person with character, not a corporate bot
✓ Add hype: Make people want to click - build excitement without being cringe
✓ Use formatting: Short lines, bullet points (•), or line breaks work great for impact
✓ Emoji: Use 0-2 emojis that fit the vibe (🔴 for live, 🔥 for hype, 🎮 for gaming, etc.)

STEP 2 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {content_max} characters or less (including hashtags)
✓ Output: ONLY the post text (no quotes, no meta-commentary, no labels)
✓ Based on title: Break down what's happening BUT don't just copy/paste the title
✓ Call-to-action: Natural invite like "come hang out", "let's build", "watch the chaos"
✗ DO NOT repost the title verbatim - the link already shows it
✗ DO NOT include the URL (it's added automatically)
✗ DO NOT invent details not in the title (no "drops enabled", "giveaways", "tonight at 7pm", etc.)
✗ DO NOT use cringe words: "INSANE", "EPIC", "smash that", "unmissable", "legendary"

STEP 3 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY 3 hashtags at the end.
- Extract hashtags from key words/topics in the title
- NEVER use the username "{username}" as a hashtag
- NEVER use generic tags (#Gaming, #Live, #Stream) unless they're in the title
- Format: space before each hashtag

EXAMPLES OF DIFFERENT STYLES:

Example 1 - Tech/Professional:
Title: "Building a Firewall | Cybersecurity & Linux"
Good: "Stream is live 🔴

Building a firewall from scratch.
Cybersecurity rants included.
Linux tinkering after.

Come hang out. #Cybersecurity #Linux #Firewall"

Example 2 - Gaming/Competitive:
Title: "Valorant Ranked Climb"
Good: "Ranked grind time.
Climbing out of plat.
Let's get it. #Valorant #Ranked #Competitive"

Example 3 - Creative/Chill:
Title: "Minecraft Creative Building"
Good: "Building something cool in Minecraft! Come share ideas and hang out 🏗️ #Minecraft #Creative #Building"

Example 4 - Casual/Fun:
Title: "Just Chatting - AMA"
Good: "Hanging out and answering your questions. Come chat! #JustChatting #AMA #Community"

Bad examples to AVOID:
✗ "EPIC stream starting NOW! INSANE gameplay! #LIVE #HYPE #GAMING" (cringe, generic)
✗ Just copying the title: "Building a Firewall | Cybersecurity & Linux #Firewall #Cyber #Linux"

NOW: Write the post for "{title}" on {platform_name}. Match the title's energy. Exactly 3 hashtags. Under {content_max} characters.

Post:"""

    @staticmethod
    def _prompt_stream_end(platform_name: str, username: str, title: str,
                           prompt_max: int, strict_mode: bool = False) -> str:
        """Build optimized prompt for stream end messages."""
        strict_prefix = ""
        if strict_mode:
            strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""

        return f"""{strict_prefix}You are a social media assistant that writes thank-you posts after streams end with personality.

TASK: Write a short, grateful post thanking viewers for watching {username}'s stream.

STREAM TITLE: "{title}"

STEP 1 - STYLE & TONE:
✓ Match the vibe: Keep the same energy as the stream (technical, gaming, casual, etc.)
✓ Be genuine: Real gratitude, not corporate-speak
✓ Keep it natural: Short, punchy, or casual - whatever fits the stream's style
✓ Emoji: Use 0-2 emojis that fit the vibe (optional)

STEP 2 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {prompt_max} characters or less (including hashtags)
✓ Output: ONLY the post text (no quotes, no meta-commentary)
✓ Based on title: Reference what was streamed BUT don't just copy/paste the title
✓ Message: Simple, genuine thank you for watching/joining
✗ DO NOT repost the title verbatim - add gratitude and personality
✗ DO NOT invent details (no "200 viewers", "raided someone", "highlight was X", "VOD soon")
✗ DO NOT mention next stream time or schedule
✗ DO NOT use exaggerated words: "AMAZING", "INCREDIBLE", "INSANE", "legendary"

STEP 3 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY 2 hashtags at the end.
- Extract hashtags from key words/topics in the title
- NEVER use the username "{username}" as a hashtag
- NEVER use generic tags unless the title has no clear words
- Format: space before each hashtag

EXAMPLES:

Example 1 - Tech/Professional:
Title: "Firewall Build | Cybersecurity"
Good: "Stream's over! Thanks for watching the firewall build. GG #Cybersecurity #Homelab"

Example 2 - Gaming:
Title: "Valorant Ranked"
Good: "Thanks for watching the ranked grind! See you next time #Valorant #Ranked"

Example 3 - Creative:
Title: "Minecraft Building"
Good: "Thanks for hanging out while I built! See you next time 🏗️ #Minecraft #Building"

Bad examples to AVOID:
✗ "AMAZING stream! 150 viewers! Raided someone! #EPIC #HYPE" (invented details, cringe)
✗ "Thanks everyone! Stream again tomorrow at 7pm!" (mentioned next stream time)

NOW: Write the thank-you post for "{title}" on {platform_name}. Match the stream's vibe. Exactly 2 hashtags. Under {prompt_max} characters.

Post:"""

    # ─────────────────────────────────────────────────────────────────────
    # Guardrail helpers — thin delegates to hypeman-social's guardrails
    # module, kept as methods because callers and tests use them here.
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_message_quality(message: str, expected_hashtag_count: int,
                                  title: str = '', username: str = ''):
        return _guardrails.validate_message_quality(
            message, expected_hashtag_count, title, username, STREAM_PROFILE)

    @staticmethod
    def _score_message_quality(message: str, title: str):
        return _guardrails.score_message_quality(message, title, STREAM_PROFILE)

    @staticmethod
    def _validate_hashtags_against_username(message: str, username: str) -> str:
        return _guardrails.validate_hashtags_against_username(message, username)

    @staticmethod
    def _validate_platform_specific(message: str, platform: str) -> list[str]:
        return _guardrails.validate_platform_specific(message, platform)

    @staticmethod
    def _contains_forbidden_words(message: str):
        return _guardrails.contains_forbidden_words(message)

    @staticmethod
    def _contains_profanity(message: str, severity: str = 'moderate'):
        return _guardrails.contains_profanity(message, severity)

    @staticmethod
    def _count_emojis(message: str) -> int:
        return _guardrails.count_emojis(message)

    @staticmethod
    def _tokenize_username(username: str):
        return _guardrails.tokenize_username(username)

    @staticmethod
    def _extract_hashtags(message: str) -> list[str]:
        return _guardrails.extract_hashtags(message)

    @staticmethod
    def _remove_hashtag_from_message(message: str, hashtag: str) -> str:
        return _guardrails.remove_hashtag_from_message(message, hashtag)

    @staticmethod
    def _safe_trim(message: str, limit: int) -> str:
        return _guardrails.safe_trim(message, limit)

    @staticmethod
    def _extract_from_thinking(thinking_content: str, max_chars: int = 300) -> str | None:
        return _guardrails.extract_from_thinking(thinking_content, max_chars)

    def _is_duplicate_message(self, message: str) -> bool:
        return self.engine.is_duplicate_message(message)

    def _add_to_message_cache(self, message: str) -> None:
        self.engine.add_to_message_cache(message)
