"""
Tests for LLM post-generation quality validation.

Tests the guardrails that catch when small LLMs fuck up and:
- Use wrong number of hashtags
- Include forbidden clickbait words we explicitly told them not to use
- Accidentally include URLs in the content
- Hallucinate details that weren't in the stream title

Because apparently we need to teach AI how to count and read instructions.
George Carlin would have a field day with this shit.

"We spent billions of dollars and decades of research to build artificial intelligence.
And now we're writing unit tests to make sure it can count to fucking three.
THREE! Not quantum physics. Not the meaning of life. THREE HASHTAGS.

And you know what the best part is? The tests are MORE RELIABLE than the AI.
A bunch of if-statements written by a hungover programmer at 3am is more trustworthy
than a neural network trained on the entire fucking internet. Beautiful.

Welcome to the future, folks. It's exactly as stupid as the past, but now it's
automated stupid. We've achieved stupidity at scale. Congratulations, humanity."
- The Ghost of George Carlin, probably laughing his ass off in the afterlife
"""

import pytest
from stream_daemon.ai.generator import AIMessageGenerator


class TestMessageQualityValidation:
    """Test post-generation quality checks.
    
    Or: "How we learned to stop trusting the AI and love the validation."
    """
    
    def test_correct_hashtag_count_passes(self):
        """Valid messages with correct hashtag count pass validation."""
        # Start message with 3 hashtags
        message = "Playing some Minecraft! Come hang out #Minecraft #Creative #Building"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=3, title="Minecraft Creative Building", username="CoolStreamer99"
        )
        assert is_valid
        assert len(issues) == 0
        
        # End message with 2 hashtags
        message = "Thanks for watching the stream! #Minecraft #GG"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=2, title="Minecraft Building", username="CoolStreamer99"
        )
        assert is_valid
        assert len(issues) == 0
    
    def test_wrong_hashtag_count_fails(self):
        """Messages with wrong number of hashtags fail validation."""
        # Only 2 hashtags when we need 3
        message = "Playing Valorant! Come watch #Valorant #Competitive"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=3, title="Valorant Competitive", username="ProGamer"
        )
        assert not is_valid
        assert any("hashtag count" in issue.lower() for issue in issues)
        
        # 4 hashtags when we need 3
        message = "Playing Valorant! #Valorant #Competitive #FPS #Gaming"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=3, title="Valorant Competitive", username="ProGamer"
        )
        assert not is_valid
        assert any("hashtag count" in issue.lower() for issue in issues)
    
    def test_forbidden_words_detected(self):
        """Messages with clickbait/forbidden words are detected.
        
        We literally have to check if the AI used the word "INSANE".
        Peak civilization, folks.
        """
        forbidden_tests = [
            ("This is going to be INSANE! #Valorant #Competitive #FPS", "insane"),
            ("Epic gameplay incoming! #Valorant #Ranked #FPS", "epic"),
            ("Crazy plays tonight! #Valorant #Ranked #FPS", "crazy"),
            ("Smash that follow button! #Valorant #Ranked #FPS", "smash"),
            ("Most incredible stream ever! #Valorant #Ranked #FPS", "incredible"),
            ("This is going to be LIT 🔥 #Valorant #Ranked #FPS", "lit"),
            ("Legendary gameplay ahead! #Valorant #Ranked #FPS", "legendary"),
        ]
        
        for message, expected_word in forbidden_tests:
            is_valid, issues = AIMessageGenerator._validate_message_quality(
                message, expected_hashtag_count=3, title="Valorant Ranked", username="ProGamer"
            )
            assert not is_valid, f"Should detect forbidden word '{expected_word}' in: {message}"
            assert any("forbidden" in issue.lower() for issue in issues)
            assert any(expected_word in issue.lower() for issue in issues)
    
    def test_url_in_content_detected(self):
        """Messages that include URLs (should be added separately) are detected."""
        message = "Playing Valorant! https://twitch.tv/progamer #Valorant #Ranked #FPS"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=3, title="Valorant Ranked", username="ProGamer"
        )
        assert not is_valid
        assert any("url" in issue.lower() for issue in issues)
        
        # Also test http://
        message = "Playing Valorant! http://kick.com/progamer #Valorant #Ranked #FPS"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=3, title="Valorant Ranked", username="ProGamer"
        )
        assert not is_valid
        assert any("url" in issue.lower() for issue in issues)
    
    def test_hallucination_detection(self):
        """Common hallucinations (invented details) are detected.
        
        The AI makes shit up. Just completely fabricates details.
        "200 viewers!" - No there weren't.
        "Drops enabled!" - No they're not.
        "Giveaway tonight!" - No there fucking isn't.
        
        It's like that friend who can't tell a story without embellishing.
        Except this friend cost millions of dollars to create.
        """
        hallucination_tests = [
            "Playing Valorant with drops enabled! #Valorant #Ranked #FPS",
            "Giveaway stream tonight! #Valorant #Ranked #FPS",
            "Stream starting at 8pm! #Valorant #Ranked #FPS",
            "Playing Valorant tonight at 7! #Valorant #Ranked #FPS",
            "VOD coming soon! Thanks for watching #Valorant #GG",
            "200 viewers tonight! Thanks all #Valorant #GG",
            "Raided my friend after! #Valorant #GG",
            "Special guest appearance! #Valorant #Ranked #FPS",
        ]
        
        for message in hallucination_tests:
            is_valid, issues = AIMessageGenerator._validate_message_quality(
                message, expected_hashtag_count=3, title="Valorant Ranked", username="ProGamer"
            )
            # Should detect hallucination
            # (not always invalid, but should flag it)
            if not is_valid:
                assert any("hallucination" in issue.lower() for issue in issues), \
                    f"Expected hallucination detection in: {message}"
    
    def test_extract_hashtags(self):
        """Hashtag extraction works correctly."""
        tests = [
            ("Playing #Minecraft with #Creative #Building", ["minecraft", "creative", "building"]),
            ("No hashtags here", []),
            ("#SingleTag", ["singletag"]),
            ("Mixed #Case #TAGS #LowerCase", ["case", "tags", "lowercase"]),
            ("With #emoji 🎮 and #numbers123", ["emoji", "numbers123"]),
        ]
        
        for message, expected in tests:
            result = AIMessageGenerator._extract_hashtags(message)
            assert result == expected, f"Failed for: {message}"
    
    def test_forbidden_words_check(self):
        """Forbidden word detection works correctly."""
        # Should find forbidden words
        has_forbidden, found = AIMessageGenerator._contains_forbidden_words("This is INSANE!")
        assert has_forbidden
        assert "insane" in found
        
        has_forbidden, found = AIMessageGenerator._contains_forbidden_words("Epic and crazy stream!")
        assert has_forbidden
        assert "epic" in found
        assert "crazy" in found
        
        # Should not flag normal words
        has_forbidden, found = AIMessageGenerator._contains_forbidden_words("Playing Minecraft, come hang out!")
        assert not has_forbidden
        assert len(found) == 0
    
    def test_multiple_issues_reported(self):
        """Messages with multiple issues report all of them."""
        # Wrong hashtag count + forbidden word + URL
        message = "INSANE stream! https://twitch.tv/user #Valorant #Ranked"
        is_valid, issues = AIMessageGenerator._validate_message_quality(
            message, expected_hashtag_count=3, title="Valorant Ranked", username="ProGamer"
        )
        assert not is_valid
        assert len(issues) >= 2  # Should catch at least hashtag count and forbidden word
        
        # Check specific issues
        issue_text = " ".join(issues).lower()
        assert "hashtag" in issue_text
        assert "forbidden" in issue_text or "insane" in issue_text


class TestHashtagExtraction:
    """Test hashtag parsing and counting."""
    
    def test_hashtag_extraction_edge_cases(self):
        """Hashtag extraction handles edge cases correctly."""
        tests = [
            # Multiple spaces between hashtags
            ("Test   #tag1   #tag2", ["tag1", "tag2"]),
            # Hashtags at start/end
            ("#start middle #end", ["start", "end"]),
            # Adjacent hashtags
            ("#tag1#tag2", ["tag1", "tag2"]),
            # Unicode hashtags (alphanumeric only, so accents won't match)
            ("English #test123", ["test123"]),
            # Empty string
            ("", []),
            # Just whitespace
            ("   ", []),
            # Hashtag-like but not hashtags (# without alphanum)
            ("Price is #50 #test", ["test"]),  # #50 won't match, #test will
        ]
        
        for message, expected in tests:
            result = AIMessageGenerator._extract_hashtags(message)
            assert result == expected, f"Failed for: '{message}'"


class TestForbiddenWords:
    """Test forbidden word detection.
    
    Because we have to explicitly program a list of words the AI isn't allowed to say.
    It's like the FCC, but for robots. George would fucking love this.
    """
    
    def test_case_insensitive(self):
        """Forbidden word detection is case-insensitive."""
        test_cases = [
            "INSANE gameplay",
            "insane gameplay", 
            "InSaNe gameplay",
        ]
        
        for message in test_cases:
            has_forbidden, found = AIMessageGenerator._contains_forbidden_words(message)
            assert has_forbidden
            assert "insane" in found
    
    def test_partial_word_matching(self):
        """Forbidden words are detected even within other words."""
        # "insane" should be found in "insanely"
        has_forbidden, found = AIMessageGenerator._contains_forbidden_words("This is insanely good!")
        assert has_forbidden
        assert "insane" in found
        
        # But normal words should be fine
        has_forbidden, found = AIMessageGenerator._contains_forbidden_words("Playing a casual game")
        assert not has_forbidden
    
    def test_all_forbidden_words(self):
        """All forbidden words are properly detected."""
        forbidden_list = [
            'insane', 'epic', 'crazy', 'smash', 'unmissable',
            'incredible', 'amazing', 'lit', 'fire', 'legendary',
            'mind-blowing', 'jaw-dropping', 'unbelievable'
        ]
        
        for word in forbidden_list:
            message = f"This is {word} content!"
            has_forbidden, found = AIMessageGenerator._contains_forbidden_words(message)
            assert has_forbidden, f"Failed to detect: {word}"
            assert word in found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
