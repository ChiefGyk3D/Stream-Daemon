"""
Test AI message generator retry logic for handling transient API errors.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from stream_daemon.ai.generator import AIMessageGenerator


class TestAIRetryLogic:
    """Test suite for AI message generator retry logic."""
    
    @pytest.fixture
    def generator(self, monkeypatch):
        """Create an AI message generator instance."""
        # Mock environment to configure Gemini provider
        monkeypatch.setenv('LLM_ENABLE', 'True')
        monkeypatch.setenv('LLM_PROVIDER', 'gemini')
        monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
        monkeypatch.setenv('LLM_MODEL', 'gemini-2.0-flash-lite')
        
        gen = AIMessageGenerator()
        gen.enabled = True
        gen.provider = 'gemini'
        gen.client = Mock()
        gen.model = 'gemini-2.0-flash-lite'
        gen.max_retries = 3
        gen.retry_delay_base = 0.1  # Short delay for testing
        return gen
    
    def test_successful_generation_no_retry(self, generator):
        """Test successful generation on first attempt (no retry needed)."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Test message content"
        generator.client.models.generate_content.return_value = mock_response
        
        result = generator._generate_with_retry("Test prompt")
        
        assert result == "Test message content"
        assert generator.client.models.generate_content.call_count == 1
    
    def test_retry_on_503_error(self, generator):
        """Test retry logic for 503 Service Unavailable errors."""
        # First two attempts fail with 503, third succeeds
        mock_response = Mock()
        mock_response.text = "Success after retry"
        
        generator.client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE. {'error': {'code': 503, 'message': 'The model is overloaded. Please try again later.', 'status': 'UNAVAILABLE'}}"),
            Exception("503 Service Unavailable"),
            mock_response
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = generator._generate_with_retry("Test prompt")
        
        assert result == "Success after retry"
        assert generator.client.models.generate_content.call_count == 3
    
    def test_retry_on_429_rate_limit(self, generator):
        """Test retry logic for 429 Rate Limit errors."""
        mock_response = Mock()
        mock_response.text = "Success after rate limit"
        
        generator.client.models.generate_content.side_effect = [
            Exception("429 Rate Limit Exceeded"),
            mock_response
        ]
        
        with patch('time.sleep'):
            result = generator._generate_with_retry("Test prompt")
        
        assert result == "Success after rate limit"
        assert generator.client.models.generate_content.call_count == 2
    
    def test_retry_on_quota_exceeded(self, generator):
        """Test retry logic for quota exceeded errors."""
        mock_response = Mock()
        mock_response.text = "Success after quota"
        
        generator.client.models.generate_content.side_effect = [
            Exception("Quota exceeded for quota metric"),
            mock_response
        ]
        
        with patch('time.sleep'):
            result = generator._generate_with_retry("Test prompt")
        
        assert result == "Success after quota"
    
    def test_no_retry_on_non_retryable_error(self, generator):
        """Test that non-retryable errors fail immediately without retry."""
        generator.client.models.generate_content.side_effect = Exception("Invalid API key")
        
        result = generator._generate_with_retry("Test prompt")
        
        assert result is None
        assert generator.client.models.generate_content.call_count == 1  # No retry
    
    def test_max_retries_exceeded(self, generator):
        """Test that retries stop after max attempts."""
        # All attempts fail with 503
        generator.client.models.generate_content.side_effect = Exception(
            "503 Service Unavailable"
        )
        
        with patch('time.sleep'):
            result = generator._generate_with_retry("Test prompt")
        
        assert result is None
        # Initial attempt + 3 retries = 4 total calls
        assert generator.client.models.generate_content.call_count == 4
    
    def test_exponential_backoff_delays(self, generator):
        """Test that delays follow exponential backoff pattern."""
        generator.retry_delay_base = 2
        generator.client.models.generate_content.side_effect = Exception("503 Unavailable")
        
        with patch('time.sleep') as mock_sleep:
            generator._generate_with_retry("Test prompt")
        
        # With rate limiting, we get:
        # - Rate limit delay (~2s) + exponential backoff (1s) = attempt 1
        # - Rate limit delay (~2s) + exponential backoff (2s) = attempt 2
        # - Rate limit delay (~2s) + exponential backoff (4s) = attempt 3
        # - Rate limit delay (~2s) = final attempt
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        
        # Filter delays: rate limiting delays are ~2s, exponential backoff are exact integers
        # We should see pattern: [~2, 1, ~2, 2, ~2, 4, ~2]
        assert len(actual_delays) == 7  # 4 attempts = 4 rate limit + 3 backoff delays
        
        # Extract exponential backoff delays (the integer ones after rate limit delays)
        backoff_delays = [actual_delays[1], actual_delays[3], actual_delays[5]]
        assert backoff_delays == [1, 2, 4]  # Verify exponential backoff: 2^0, 2^1, 2^2
    
    def test_timeout_error_is_retryable(self, generator):
        """Test that timeout errors are retried."""
        mock_response = Mock()
        mock_response.text = "Success after timeout"
        
        generator.client.models.generate_content.side_effect = [
            Exception("Request timeout"),
            mock_response
        ]
        
        with patch('time.sleep'):
            result = generator._generate_with_retry("Test prompt")
        
        assert result == "Success after timeout"
        assert generator.client.models.generate_content.call_count == 2
    
    def test_overloaded_keyword_detection(self, generator):
        """Test detection of 'overloaded' keyword in error message."""
        mock_response = Mock()
        mock_response.text = "Success"
        
        generator.client.models.generate_content.side_effect = [
            Exception("The model is overloaded. Please try again later."),
            mock_response
        ]
        
        with patch('time.sleep'):
            result = generator._generate_with_retry("Test prompt")
        
        assert result == "Success"
    
    def test_custom_max_retries(self, generator):
        """Test using custom max_retries parameter."""
        generator.client.models.generate_content.side_effect = Exception("503 Unavailable")
        
        with patch('time.sleep'):
            result = generator._generate_with_retry("Test prompt", max_retries=1)
        
        assert result is None
        # Initial + 1 retry = 2 calls
        assert generator.client.models.generate_content.call_count == 2
    
    @patch('stream_daemon.ai.generator.get_config')
    def test_retry_config_from_env(self, mock_get_config):
        """Test that retry config is loaded from environment."""
        mock_get_config.side_effect = lambda section, key, default=None: {
            ('LLM', 'max_retries'): '5',
            ('LLM', 'retry_delay_base'): '3',
        }.get((section, key), default)
        
        gen = AIMessageGenerator()
        
        assert gen.max_retries == 5
        assert gen.retry_delay_base == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
