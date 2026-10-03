# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AI generator failure handling.

Transport-level retry/backoff/reconnect logic now lives in hypeman-social
(BaseLLM.generate) and is covered by the library's own test suite. What the
daemon owns — and what these tests cover — is the layer above: delegation to
the engine, the strict-prompt retry when guardrails flag a message, and
falling back cleanly when the engine gives up.
"""

from unittest.mock import Mock

import pytest

from stream_daemon.ai.generator import AIMessageGenerator


@pytest.fixture
def generator():
    gen = AIMessageGenerator()
    gen.enabled = True
    gen.engine = Mock()
    gen.engine.enable_deduplication = False
    gen.engine.is_duplicate_message.return_value = False
    return gen


GOOD_MESSAGE = "Firewall build stream is live, come hang out #Firewall #Linux #Homelab"
URL = "https://twitch.tv/chief"


class TestEngineDelegation:
    def test_generate_with_retry_delegates_to_engine(self, generator):
        generator.engine.generate.return_value = "hello"
        assert generator._generate_with_retry("prompt") == "hello"
        generator.engine.generate.assert_called_once_with("prompt")

    def test_engine_failure_returns_none(self, generator):
        """Engine exhausted its retries/fallbacks -> daemon falls back to templates."""
        generator.engine.generate.return_value = None
        result = generator.generate_stream_start_message(
            "Twitch", "chief", "Firewall Build", URL, "bluesky")
        assert result is None

    def test_disabled_generator_never_calls_engine(self, generator):
        generator.enabled = False
        assert generator.generate_stream_start_message(
            "Twitch", "chief", "Title", URL) is None
        generator.engine.generate.assert_not_called()


class TestStartMessageFlow:
    def test_successful_generation_appends_url(self, generator):
        generator.engine.generate.return_value = GOOD_MESSAGE
        result = generator.generate_stream_start_message(
            "Twitch", "chief", "Firewall Build | Linux", URL, "bluesky")
        assert result is not None
        assert result.endswith(f"\n\n{URL}")
        assert GOOD_MESSAGE in result

    def test_single_generation_when_message_is_clean(self, generator):
        generator.engine.generate.return_value = GOOD_MESSAGE
        generator.generate_stream_start_message(
            "Twitch", "chief", "Firewall Build | Linux", URL, "bluesky")
        assert generator.engine.generate.call_count == 1

    def test_guardrail_issue_triggers_strict_retry(self, generator):
        # First attempt has 4 hashtags (expected exactly 3); retry is clean.
        bad = "Live now! #One #Two #Three #Four"
        generator.engine.generate.side_effect = [bad, GOOD_MESSAGE]

        result = generator.generate_stream_start_message(
            "Twitch", "chief", "Firewall Build | Linux", URL, "bluesky")

        assert generator.engine.generate.call_count == 2
        strict_prompt = generator.engine.generate.call_args_list[1][0][0]
        assert "CRITICAL" in strict_prompt
        assert GOOD_MESSAGE in result

    def test_original_kept_when_strict_retry_also_flagged(self, generator):
        """Lenient philosophy: minor issues beat posting nothing."""
        bad = "Live now! #One #Two #Three #Four"
        generator.engine.generate.side_effect = [bad, bad]

        result = generator.generate_stream_start_message(
            "Twitch", "chief", "Firewall Build | Linux", URL, "bluesky")

        assert result is not None
        assert bad in result

    def test_bluesky_content_capped_at_limit(self, generator):
        generator.engine.generate.return_value = "w" * 400
        result = generator.generate_stream_start_message(
            "Twitch", "chief", "Title", URL, "bluesky")
        assert result is not None
        assert len(result) <= generator.bluesky_max_chars

    def test_profanity_vetoes_when_filter_enabled(self, generator):
        generator.enable_profanity_filter = True
        profane = "Get your ass in here, stream is live #Live #Now #Chaos"
        generator.engine.generate.side_effect = [profane, profane]
        result = generator.generate_stream_start_message(
            "Twitch", "chief", "Title", URL, "mastodon")
        assert result is None


class TestEndMessageFlow:
    def test_end_message_has_no_url(self, generator):
        message = "Thanks for watching the firewall build! GG #Firewall #Linux"
        generator.engine.generate.return_value = message
        result = generator.generate_stream_end_message(
            "Twitch", "chief", "Firewall Build | Linux", "bluesky")
        assert result == message

    def test_none_title_defaults_to_stream(self, generator):
        generator.engine.generate.return_value = "Thanks for watching! #GG #Stream"
        result = generator.generate_stream_end_message("Twitch", "chief", None, "bluesky")
        assert result is not None
        prompt = generator.engine.generate.call_args_list[0][0][0]
        assert '"Stream"' in prompt
