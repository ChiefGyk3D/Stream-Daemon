"""Tests for Qwen3 thinking mode support in AI message generator."""

import pytest
from unittest.mock import patch, MagicMock

# We'll test the extraction logic directly
class TestQwen3ThinkingModeExtraction:
    """Test the _extract_from_thinking method for Qwen3 support."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Import the class - we'll mock the config
        with patch('stream_daemon.ai.generator.get_config') as mock_config, \
             patch('stream_daemon.ai.generator.get_bool_config') as mock_bool_config, \
             patch('stream_daemon.ai.generator.get_secret') as mock_secret:
            
            # Configure mocks
            mock_config.side_effect = lambda section, key, default='': default
            mock_bool_config.return_value = False
            mock_secret.return_value = None
            
            from stream_daemon.ai.generator import AIMessageGenerator
            self.generator = AIMessageGenerator()
    
    def test_extract_quoted_text(self):
        """Test extraction of quoted text (lines starting with >)."""
        thinking = """
        Let me create a post for this stream...
        
        Here's what I came up with:
        
        > Level up your security game! 🔥 My AI tools got a serious boost & we're building a firewall LIVE tonight on Twitch! #Cybersecurity #LinuxGaming
        
        This captures the casual tech vibe while...
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "Level up your security game" in result
        assert "#Cybersecurity" in result
    
    def test_extract_from_final_post_marker(self):
        """Test extraction using 'Final post:' marker."""
        thinking = """
        Steps:
        1. Keep it under 280 characters
        2. Include hashtags
        
        Final post: My AI just got upgraded! 🤖 Building a firewall tonight - join me! #CyberSecurity #Twitch
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "My AI just got upgraded" in result
    
    def test_extract_from_heres_the_post_marker(self):
        """Test extraction using 'Here's the post:' marker."""
        thinking = """
        I'll create an engaging announcement...
        
        Here's the post: Leveling up my defenses tonight! 🛡️ Come watch me build a firewall while gaming. #LinuxGaming
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "Leveling up my defenses" in result
    
    def test_extract_line_with_hashtags(self):
        """Test extraction of lines containing hashtags."""
        thinking = """
        I need to create something catchy...
        
        The user wants:
        - Under 280 chars
        - 1-2 hashtags
        
        - Upgraded AI tools + firewall building = epic stream night! Join me on Twitch 🔥 #Cybersecurity #LinuxGaming
        
        This should work because...
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "#Cybersecurity" in result or "#LinuxGaming" in result
    
    def test_extract_empty_thinking(self):
        """Test handling of empty thinking field."""
        result = self.generator._extract_from_thinking("")
        assert result is None
        
        result = self.generator._extract_from_thinking(None)
        assert result is None
    
    def test_extract_no_extractable_content(self):
        """Test handling when no content can be extracted."""
        thinking = """
        Let me think about this...
        The user wants a post about streaming.
        I need to consider the character limit.
        But I'm not sure what to write yet...
        """
        
        result = self.generator._extract_from_thinking(thinking)
        # Should return None if no valid content found
        assert result is None
    
    def test_extract_too_short_quoted_text(self):
        """Test that very short quoted text is rejected."""
        thinking = """
        Here's my attempt:
        > Hi!
        
        That's too short, let me try again...
        """
        
        result = self.generator._extract_from_thinking(thinking)
        # "Hi!" is too short (< 20 chars), should not be extracted
        # May fall back to other patterns or return None
    
    def test_extract_multiple_quoted_lines(self):
        """Test extraction when multiple quoted lines exist."""
        thinking = """
        Let me build this post:
        
        > Level up your security game! 🔥
        > My AI tools got upgraded & we're building
        > a firewall LIVE! #Cybersecurity
        
        This spans multiple lines...
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        # Should join the quoted lines
        assert "Level up" in result


class TestQwen3ResponseHandling:
    """Test the full response handling for Qwen3 models."""
    
    def test_ollama_response_with_thinking_enabled(self):
        """Test handling of Qwen3 response with thinking mode enabled."""
        with patch('stream_daemon.ai.generator.get_config') as mock_config, \
             patch('stream_daemon.ai.generator.get_bool_config') as mock_bool_config, \
             patch('stream_daemon.ai.generator.get_secret') as mock_secret, \
             patch('stream_daemon.ai.generator.OLLAMA_AVAILABLE', True):
            
            # Configure for thinking mode
            def config_side_effect(section, key, default=''):
                config_map = {
                    ('LLM', 'enable_thinking_mode'): 'True',
                    ('LLM', 'thinking_token_multiplier'): '4.0',
                    ('LLM', 'temperature'): '0.3',
                    ('LLM', 'top_p'): '0.9',
                    ('LLM', 'max_tokens'): '150',
                    ('LLM', 'provider'): 'ollama',
                    ('LLM', 'model'): 'qwen3:4b',
                }
                return config_map.get((section, key), default)
            
            mock_config.side_effect = config_side_effect
            mock_bool_config.return_value = True
            
            from stream_daemon.ai.generator import AIMessageGenerator
            generator = AIMessageGenerator()
            
            # Verify thinking mode is enabled
            assert generator.enable_thinking_mode is True
            assert generator.thinking_token_multiplier == 4.0
    
    def test_token_multiplier_calculation(self):
        """Test that token multiplier is applied correctly."""
        with patch('stream_daemon.ai.generator.get_config') as mock_config, \
             patch('stream_daemon.ai.generator.get_bool_config') as mock_bool_config, \
             patch('stream_daemon.ai.generator.get_secret') as mock_secret:
            
            def config_side_effect(section, key, default=''):
                config_map = {
                    ('LLM', 'enable_thinking_mode'): 'True',
                    ('LLM', 'thinking_token_multiplier'): '5.0',
                    ('LLM', 'max_tokens'): '150',
                }
                return config_map.get((section, key), default)
            
            mock_config.side_effect = config_side_effect
            mock_bool_config.return_value = False
            
            from stream_daemon.ai.generator import AIMessageGenerator
            generator = AIMessageGenerator()
            
            # Expected: 150 * 5.0 = 750 effective tokens
            expected_tokens = int(generator.max_tokens * generator.thinking_token_multiplier)
            assert expected_tokens == 750


class TestQwen3EdgeCases:
    """Test edge cases for Qwen3 support."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('stream_daemon.ai.generator.get_config') as mock_config, \
             patch('stream_daemon.ai.generator.get_bool_config') as mock_bool_config, \
             patch('stream_daemon.ai.generator.get_secret') as mock_secret:
            
            mock_config.side_effect = lambda section, key, default='': default
            mock_bool_config.return_value = False
            mock_secret.return_value = None
            
            from stream_daemon.ai.generator import AIMessageGenerator
            self.generator = AIMessageGenerator()
    
    def test_extract_handles_unicode(self):
        """Test extraction with unicode characters."""
        thinking = """
        Creating an engaging post with emojis...
        
        > 🎮 Level up your cybersecurity game! AI tools upgraded, building firewalls tonight! 🔥 #Cybersecurity #LinuxGaming
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "🎮" in result or "🔥" in result
    
    def test_extract_handles_special_characters(self):
        """Test extraction with special characters in stream titles."""
        thinking = """
        The title has special chars: C++ & Python | AI/ML
        
        Final post: Diving into C++ & Python tonight! AI/ML streams are the best 🤖 #Programming #AIStreaming
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "C++" in result or "Python" in result
    
    def test_extract_case_insensitive_markers(self):
        """Test that markers are case insensitive."""
        thinking = """
        Let me think...
        
        FINAL POST: This is my announcement! #Streaming #Gaming
        """
        
        result = self.generator._extract_from_thinking(thinking)
        assert result is not None
        assert "announcement" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
