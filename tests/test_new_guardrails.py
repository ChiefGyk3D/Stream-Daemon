"""
Test suite for the new LLM guardrails added to Stream-Daemon.

Because we spent all this time implementing guardrails to babysit an AI,
and now we need to test if our AI babysitter works correctly. It's AI
supervision all the way down, folks.

This tests:
- Message deduplication (detecting similar messages)
- Emoji counting (yes, we teach computers to count emojis)
- Profanity filtering (the seven words you can't say... to an AI)
- Quality scoring (grading AI's homework)
- Platform-specific validation (each platform's special fucking snowflake rules)
"""

import pytest
from stream_daemon.ai.generator import AIMessageGenerator


class TestMessageDeduplication:
    """Test that we can detect when AI is repeating itself like your drunk uncle."""
    
    def test_exact_duplicate_detected(self):
        """Exact same message should be flagged as duplicate."""
        gen = AIMessageGenerator()
        
        message1 = "Playing Valorant! Come watch #Valorant #FPS #Gaming"
        message2 = "Playing Valorant! Come watch #Valorant #FPS #Gaming"
        
        # Add first message to cache
        gen._add_to_message_cache(message1)
        
        # Check if second message is duplicate
        assert gen._is_duplicate_message(message2) is True
    
    def test_similar_message_detected(self):
        """Very similar messages should be flagged as duplicates."""
        gen = AIMessageGenerator()
        
        message1 = "Playing Valorant ranked games! #Valorant #Competitive #FPS"
        message2 = "Playing Valorant ranked games! #Valorant #Ranked #FPS"
        
        gen._add_to_message_cache(message1)
        
        # Should detect >80% similarity
        # (These messages share most words, only hashtag difference)
        assert gen._is_duplicate_message(message2) is True
    
    def test_different_message_not_duplicate(self):
        """Different messages should not be flagged as duplicates."""
        gen = AIMessageGenerator()
        
        message1 = "Playing Valorant ranked! #Valorant #Competitive #FPS"
        message2 = "Building in Minecraft! #Minecraft #Creative #Building"
        
        gen._add_to_message_cache(message1)
        
        assert gen._is_duplicate_message(message2) is False
    
    def test_cache_size_limit(self):
        """Cache should respect size limit (FIFO)."""
        gen = AIMessageGenerator()
        gen.dedup_cache_size = 3  # Set small cache for testing
        
        messages = [
            "Message 1 #Gaming",
            "Message 2 #Streaming", 
            "Message 3 #Live",
            "Message 4 #Content"
        ]
        
        # Add all messages
        for msg in messages:
            gen._add_to_message_cache(msg)
        
        # Cache should only have last 3
        assert len(gen._message_cache) == 3
        assert "Message 1 #Gaming" not in gen._message_cache
        assert "Message 4 #Content" in gen._message_cache


class TestEmojiCounting:
    """Test that we can count tiny pictures. Peak civilization."""
    
    def test_no_emojis(self):
        """Message with no emojis should return 0."""
        gen = AIMessageGenerator()
        message = "Playing games! #Gaming #Fun"
        
        assert gen._count_emojis(message) == 0
    
    def test_single_emoji(self):
        """Message with one emoji should return 1."""
        gen = AIMessageGenerator()
        message = "Playing games! 🎮 #Gaming"
        
        assert gen._count_emojis(message) == 1
    
    def test_multiple_emojis(self):
        """Message with multiple emojis should count them all."""
        gen = AIMessageGenerator()
        message = "Playing games! 🎮🔥💪 #Gaming"
        
        assert gen._count_emojis(message) == 3
    
    def test_mixed_content_with_emojis(self):
        """Emojis mixed with text should be counted correctly."""
        gen = AIMessageGenerator()
        message = "Let's go! 🚀 Playing Valorant 🎮 ranked! 💪 #Valorant"
        
        assert gen._count_emojis(message) == 3


class TestProfanityFilter:
    """Test the seven words you can't say to an AI. RIP George Carlin."""
    
    def test_no_profanity_clean_message(self):
        """Clean message should pass all severity levels."""
        gen = AIMessageGenerator()
        message = "Playing games with friends! #Gaming"
        
        assert gen._contains_profanity(message, "mild") == (False, [])
        assert gen._contains_profanity(message, "moderate") == (False, [])
        assert gen._contains_profanity(message, "severe") == (False, [])
    
    def test_severe_profanity_detected(self):
        """Severe profanity should be detected at all levels."""
        gen = AIMessageGenerator()
        message = "Playing this fucking game"
        
        has_prof, words = gen._contains_profanity(message, "severe")
        assert has_prof is True
        assert "fucking" in words
    
    def test_moderate_profanity_detected(self):
        """Moderate profanity should be detected at moderate and severe levels."""
        gen = AIMessageGenerator()
        message = "This game is crap"
        
        # Should detect at moderate level
        has_prof, words = gen._contains_profanity(message, "moderate")
        assert has_prof is True
        
        # Should also detect at severe level
        has_prof, words = gen._contains_profanity(message, "severe")
        assert has_prof is True
    
    def test_mild_profanity_not_detected_at_moderate(self):
        """Test profanity severity levels work correctly."""
        gen = AIMessageGenerator()
        
        # "fuck" is in severe list (most severe)
        # Should be caught only at severe level
        message_severe_word = "This fucking game"
        assert gen._contains_profanity(message_severe_word, "mild")[0] is False
        assert gen._contains_profanity(message_severe_word, "moderate")[0] is False  
        assert gen._contains_profanity(message_severe_word, "severe")[0] is True
        
        # "ass" is in moderate list
        # Should be caught at moderate and severe, but NOT mild
        message_moderate_word = "This game is ass"
        assert gen._contains_profanity(message_moderate_word, "mild")[0] is False
        assert gen._contains_profanity(message_moderate_word, "moderate")[0] is True
        assert gen._contains_profanity(message_moderate_word, "severe")[0] is True
        
        # "damn" is in mild list (least severe)
        # Should be caught at ALL levels
        message_mild_word = "This damn game"
        assert gen._contains_profanity(message_mild_word, "mild")[0] is True
        assert gen._contains_profanity(message_mild_word, "moderate")[0] is True
        assert gen._contains_profanity(message_mild_word, "severe")[0] is True
    
    def test_word_boundary_matching(self):
        """Profanity filter should respect word boundaries."""
        gen = AIMessageGenerator()
        
        # "bass" contains "ass" but shouldn't match
        message = "Playing bass guitar"
        has_prof, words = gen._contains_profanity(message, "severe")
        assert has_prof is False


class TestForbiddenWords:
    """Test that forbidden words are properly detected with word boundaries."""
    
    def test_forbidden_word_detected(self):
        """Forbidden words should be detected when used as standalone words."""
        gen = AIMessageGenerator()
        
        # "fire" as a standalone word should be caught
        message = "This stream is fire! #Gaming"
        has_forbidden, words = gen._contains_forbidden_words(message)
        assert has_forbidden is True
        assert "fire" in words
    
    def test_technical_terms_not_blocked(self):
        """Technical terms containing forbidden words should NOT be blocked."""
        gen = AIMessageGenerator()
        
        # "firewall" contains "fire" but should pass
        message = "Configuring firewall rules in pfSense! #Networking #Security"
        has_forbidden, words = gen._contains_forbidden_words(message)
        assert has_forbidden is False
        
        # "firefox" contains "fire" but should pass
        message = "Testing my site in Firefox browser #WebDev"
        has_forbidden, words = gen._contains_forbidden_words(message)
        assert has_forbidden is False
        
        # "campfire" contains "fire" but should pass
        message = "Building a campfire in the game #Survival"
        has_forbidden, words = gen._contains_forbidden_words(message)
        assert has_forbidden is False
    
    def test_word_boundary_matching_forbidden(self):
        """Forbidden words should respect word boundaries like profanity filter."""
        gen = AIMessageGenerator()
        
        # "legendary" in "non-legendary" should still be caught (word boundary after 'legendary')
        message = "Testing legendary items #Gaming"
        has_forbidden, words = gen._contains_forbidden_words(message)
        assert has_forbidden is True
        assert "legendary" in words
        
        # But compound words should pass
        message = "The smashing pumpkins #Music"
        has_forbidden, words = gen._contains_forbidden_words(message)
        # "smashing" contains "smash" but is a different word
        # This should pass since we're matching whole words
        assert has_forbidden is False


class TestQualityScoring:
    """Test AI homework grading. Because that's what we've become."""
    
    def test_perfect_message_high_score(self):
        """Well-crafted message should score high."""
        gen = AIMessageGenerator()
        message = "Playing Valorant ranked! Come join the climb 🎮 #Valorant #Competitive #FPS"
        title = "Valorant Ranked"
        
        score, issues = gen._score_message_quality(message, title)
        
        # Should score 8+ (no major issues)
        assert score >= 8
        assert len(issues) == 0
    
    def test_generic_phrases_deduction(self):
        """Too many generic phrases should lower the score."""
        gen = AIMessageGenerator()
        # Use 3+ generic phrases to trigger the penalty (>2 needed)
        message = "Come hang out! Let's go! Join me! Thanks for watching! See you next time! #Gaming"
        title = "Gaming Stream"
        
        score, issues = gen._score_message_quality(message, title)
        
        # Should have deductions for too many generic phrases
        assert score < 8
        assert any("generic" in issue.lower() for issue in issues)
    
    def test_wrong_length_deduction(self):
        """Messages that are too short or too long should be penalized."""
        gen = AIMessageGenerator()
        
        # Too short
        short_message = "Stream! #Game"
        score, issues = gen._score_message_quality(short_message, "Gaming")
        assert score < 8
        assert any("too short" in issue.lower() for issue in issues)
        
        # Too long
        long_message = "A" * 400  # Way too long
        score, issues = gen._score_message_quality(long_message, "Gaming")
        assert score < 8
    
    def test_missing_title_reference_deduction(self):
        """Message should reference the stream title."""
        gen = AIMessageGenerator()
        message = "Come watch me play! #Gaming #Fun #Live"
        title = "Valorant Ranked Grind"
        
        score, issues = gen._score_message_quality(message, title)
        
        # Should penalize for not mentioning "Valorant" 
        assert score < 8
        assert any("title" in issue.lower() for issue in issues)
    
    def test_repeated_words_deduction(self):
        """Excessive word repetition should be penalized."""
        gen = AIMessageGenerator()
        message = "Playing games! Come play games! Games games games! #Gaming"
        title = "Gaming"
        
        score, issues = gen._score_message_quality(message, title)
        
        # Should detect repetition
        assert score < 8
        assert any("repeat" in issue.lower() for issue in issues)


class TestPlatformSpecificValidation:
    """Test that each platform's special snowflake rules are enforced."""
    
    def test_discord_markdown_validation(self):
        """Discord messages should have valid markdown."""
        gen = AIMessageGenerator()
        
        # Valid markdown
        valid_message = "Playing **Valorant** ranked! #Gaming"
        issues = gen._validate_platform_specific(valid_message, "discord")
        assert len(issues) == 0
        
        # Invalid markdown (unmatched bold)
        invalid_message = "Playing **Valorant ranked! #Gaming"
        issues = gen._validate_platform_specific(invalid_message, "discord")
        assert len(issues) > 0
        assert any("markdown" in issue.lower() for issue in issues)
    
    def test_discord_mention_validation(self):
        """Discord @everyone and @here should be flagged."""
        gen = AIMessageGenerator()
        
        message = "Come watch @everyone! #Gaming"
        issues = gen._validate_platform_specific(message, "discord")
        
        assert len(issues) > 0
        assert any("@everyone" in issue or "@here" in issue for issue in issues)
    
    def test_bluesky_url_in_content(self):
        """Bluesky should not have bare URLs in content (uses facets)."""
        gen = AIMessageGenerator()
        
        # URL in content
        message = "Check out my stream at https://twitch.tv/user! #Gaming"
        issues = gen._validate_platform_specific(message, "bluesky")
        
        assert len(issues) > 0
        assert any("url" in issue.lower() for issue in issues)
    
    def test_bluesky_handle_validation(self):
        """Bluesky handles should be properly formatted."""
        gen = AIMessageGenerator()
        
        # Invalid handle format
        message = "Follow me @user #Gaming"
        issues = gen._validate_platform_specific(message, "bluesky")
        
        # Should flag invalid handle (missing .bsky.social)
        assert len(issues) > 0
    
    def test_mastodon_html_entities(self):
        """Mastodon should not have unescaped HTML entities."""
        gen = AIMessageGenerator()
        
        # HTML entities that should be escaped
        message = "Playing games &amp; having fun! #Gaming"
        issues = gen._validate_platform_specific(message, "mastodon")
        
        # Should flag HTML
        assert len(issues) > 0
        assert any("html" in issue.lower() for issue in issues)
    
    def test_unknown_platform_no_validation(self):
        """Unknown platforms should skip validation."""
        gen = AIMessageGenerator()
        
        message = "Any content here @everyone <html> #Whatever"
        issues = gen._validate_platform_specific(message, "unknown_platform")
        
        # Should return empty list for unknown platforms
        assert len(issues) == 0


class TestIntegratedGuardrails:
    """Test that all guardrails work together in the actual generation flow."""
    
    @pytest.mark.skipif(
        True,  # Skip by default since it requires LLM setup
        reason="Requires LLM configuration and API access"
    )
    def test_generation_with_all_guardrails_enabled(self):
        """
        Integration test: Generate message with all guardrails active.
        
        This test is skipped by default because it requires:
        - LLM_ENABLE=True
        - LLM_PROVIDER configured (ollama or gemini)
        - Valid API credentials
        
        To run this test, configure your environment and remove the skipif.
        """
        gen = AIMessageGenerator()
        
        # Enable all guardrails
        gen.enable_deduplication = True
        gen.enable_quality_scoring = True
        gen.max_emoji_count = 2
        gen.enable_profanity_filter = True
        gen.enable_platform_validation = True
        
        # Generate a message
        message = gen.generate_stream_start_message(
            platform_name="twitch",
            username="testuser",
            title="Valorant Ranked Grind",
            url="https://twitch.tv/testuser",
            social_platform="mastodon"
        )
        
        # Verify message passes all guardrails
        assert message is not None
        assert len(message) > 0
        
        # Check emoji count
        emoji_count = gen._count_emojis(message)
        assert emoji_count <= gen.max_emoji_count
        
        # Check profanity
        has_prof, _ = gen._contains_profanity(message, gen.profanity_severity)
        assert has_prof is False
        
        # Check quality
        score, issues = gen._score_message_quality(message, "Valorant Ranked Grind")
        assert score >= gen.min_quality_score or len(issues) == 0


if __name__ == "__main__":
    """
    Run tests directly with: python tests/test_new_guardrails.py
    Or with pytest: pytest tests/test_new_guardrails.py -v
    """
    pytest.main([__file__, "-v"])
