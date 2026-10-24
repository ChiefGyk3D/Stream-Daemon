"""Required-secret guard: placeholders and empty values fail closed.

One placeholder rule (stream_daemon.config.secrets.is_placeholder) is used by
the get_secret wrapper and by the startup preflight. No test sends a request:
every secret comes from monkeypatched environment variables and
SECRETS_MANAGER is forced to 'none'.
"""

import logging

import pytest

from stream_daemon.config import preflight, secrets

REAL = "k3Jd9sLq2VxP7mTz"  # random-looking, not a placeholder

ENV_VARS = [
    'DOPPLER_TOKEN', 'SECRETS_MANAGER', 'SECRETS_VAULT_TOKEN',
    'MASTODON_ENABLE_POSTING', 'MASTODON_ACCESS_TOKEN', 'MASTODON_CLIENT_ID',
    'MASTODON_CLIENT_SECRET', 'BLUESKY_ENABLE_POSTING', 'BLUESKY_APP_PASSWORD',
    'DISCORD_ENABLE_POSTING', 'DISCORD_WEBHOOK_URL', 'DISCORD_WEBHOOK_TWITCH',
    'MATRIX_ENABLE_POSTING', 'MATRIX_PASSWORD', 'MATRIX_ACCESS_TOKEN',
    'LLM_ENABLE', 'LLM_PROVIDER', 'LLM_FALLBACK_PROVIDER', 'LLM_GEMINI_API_KEY',
    'GEMINI_API_KEY', 'TWITCH_CLIENT_ID',
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('SECRETS_MANAGER', 'none')


PLACEHOLDERS = [
    '', '   ', 'your_mastodon_access_token', 'YOUR_TWITCH_CLIENT_SECRET',
    'Your_Bot_Password', 'changeme', 'CHANGEME123', 'ChangeMe!', '<token>',
    'example', 'PLACEHOLDER', 'xxx', 'xxxxxxxx', 'dp.st.your_token_here',
    'https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN',
    None,
]


@pytest.mark.parametrize('value', PLACEHOLDERS)
def test_placeholder_rule_rejects(value):
    assert secrets.is_placeholder(value) is True


@pytest.mark.parametrize('value', [
    REAL, 'dp.st.prod.' + REAL, 'abcd1234efgh5678',
    'https://discord.com/api/webhooks/123456789/' + REAL,
])
def test_placeholder_rule_accepts_real_looking(value):
    assert secrets.is_placeholder(value) is False


def test_get_secret_rejects_lowercase_placeholder(monkeypatch, caplog):
    # The library only rejects the upper-case YOUR_ prefix; the wrapper must
    # also reject the lower-case your_ form the example file ships.
    monkeypatch.setenv('MASTODON_ACCESS_TOKEN', 'your_mastodon_access_token')
    with caplog.at_level(logging.WARNING):
        assert secrets.get_secret('Mastodon', 'access_token') is None
    assert 'MASTODON_ACCESS_TOKEN' in caplog.text
    assert 'your_mastodon_access_token' not in caplog.text


def test_get_secret_accepts_real_value(monkeypatch):
    monkeypatch.setenv('MASTODON_ACCESS_TOKEN', REAL)
    assert secrets.get_secret('Mastodon', 'access_token') == REAL


def test_nothing_enabled_no_problems():
    assert preflight.check_required_secrets() == []


def _enable(monkeypatch, name):
    monkeypatch.setenv(f'{name}_ENABLE_POSTING', 'True')


@pytest.mark.parametrize('platform, var', [
    ('MASTODON', 'MASTODON_ACCESS_TOKEN'),
    ('BLUESKY', 'BLUESKY_APP_PASSWORD'),
])
@pytest.mark.parametrize('value', [None, '', 'your_secret_here', 'YOUR_SECRET', 'changeme'])
def test_enabled_platform_bad_secret_is_a_problem(monkeypatch, platform, var, value):
    _enable(monkeypatch, platform)
    if value is not None:
        monkeypatch.setenv(var, value)
    problems = preflight.check_required_secrets()
    assert len(problems) == 1
    assert var in problems[0]
    if value:
        assert value not in problems[0]


def test_enabled_platform_real_secret_ok(monkeypatch):
    _enable(monkeypatch, 'MASTODON')
    monkeypatch.setenv('MASTODON_ACCESS_TOKEN', REAL)
    assert preflight.check_required_secrets() == []


def test_disabled_platform_placeholder_is_ignored(monkeypatch):
    monkeypatch.setenv('MASTODON_ACCESS_TOKEN', 'your_mastodon_access_token')
    assert preflight.check_required_secrets() == []


def test_mastodon_optional_pair_placeholder_rejected(monkeypatch):
    _enable(monkeypatch, 'MASTODON')
    monkeypatch.setenv('MASTODON_ACCESS_TOKEN', REAL)
    monkeypatch.setenv('MASTODON_CLIENT_ID', 'your_mastodon_client_id')
    problems = preflight.check_required_secrets()
    assert len(problems) == 1 and 'MASTODON_CLIENT_ID' in problems[0]


def test_discord_placeholder_webhook_rejected(monkeypatch):
    _enable(monkeypatch, 'DISCORD')
    hook = 'https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN'
    monkeypatch.setenv('DISCORD_WEBHOOK_URL', hook)
    problems = preflight.check_required_secrets()
    assert problems and all('DISCORD_WEBHOOK_URL' in p for p in problems)
    assert all('YOUR_WEBHOOK_TOKEN' not in p for p in problems)


def test_discord_needs_one_webhook(monkeypatch):
    _enable(monkeypatch, 'DISCORD')
    assert preflight.check_required_secrets()
    monkeypatch.setenv('DISCORD_WEBHOOK_TWITCH', 'https://discord.com/api/webhooks/1/' + REAL)
    assert preflight.check_required_secrets() == []


def test_matrix_needs_password_or_token(monkeypatch):
    _enable(monkeypatch, 'MATRIX')
    assert preflight.check_required_secrets()
    monkeypatch.setenv('MATRIX_ACCESS_TOKEN', REAL)
    assert preflight.check_required_secrets() == []


def test_matrix_placeholder_password_rejected_even_with_token(monkeypatch):
    # The library logs in with username+password whenever both are set.
    _enable(monkeypatch, 'MATRIX')
    monkeypatch.setenv('MATRIX_ACCESS_TOKEN', REAL)
    monkeypatch.setenv('MATRIX_PASSWORD', 'your_bot_password')
    problems = preflight.check_required_secrets()
    assert len(problems) == 1 and 'MATRIX_PASSWORD' in problems[0]
    assert 'your_bot_password' not in problems[0]


def test_gemini_enabled_placeholder_key_rejected(monkeypatch):
    monkeypatch.setenv('LLM_ENABLE', 'True')
    monkeypatch.setenv('LLM_PROVIDER', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'your_gemini_api_key_here')
    problems = preflight.check_required_secrets()
    assert len(problems) == 1 and 'GEMINI_API_KEY' in problems[0]
    assert 'your_gemini_api_key_here' not in problems[0]
    monkeypatch.setenv('GEMINI_API_KEY', REAL)
    assert preflight.check_required_secrets() == []


def test_gemini_as_fallback_is_checked(monkeypatch):
    monkeypatch.setenv('LLM_ENABLE', 'True')
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    monkeypatch.setenv('LLM_FALLBACK_PROVIDER', 'gemini')
    assert preflight.check_required_secrets()


def test_ollama_needs_no_key(monkeypatch):
    monkeypatch.setenv('LLM_ENABLE', 'True')
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    assert preflight.check_required_secrets() == []


def test_llm_disabled_ignores_gemini_placeholder(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'your_gemini_api_key_here')
    assert preflight.check_required_secrets() == []


def test_placeholder_doppler_token_rejected(monkeypatch):
    monkeypatch.setenv('DOPPLER_TOKEN', 'dp.st.your_token_here')
    problems = preflight.check_required_secrets()
    assert len(problems) == 1 and 'DOPPLER_TOKEN' in problems[0]
    assert 'your_token_here' not in problems[0]


def test_placeholder_vault_token_rejected(monkeypatch):
    monkeypatch.setenv('SECRETS_MANAGER', 'vault')
    monkeypatch.setenv('SECRETS_VAULT_TOKEN', 'your_vault_token')
    problems = preflight.check_required_secrets()
    assert len(problems) == 1 and 'SECRETS_VAULT_TOKEN' in problems[0]


def test_vault_token_ignored_when_vault_not_selected(monkeypatch):
    monkeypatch.setenv('SECRETS_VAULT_TOKEN', 'your_vault_token')
    assert preflight.check_required_secrets() == []


def test_enforce_exits_without_echoing_value(monkeypatch, caplog):
    _enable(monkeypatch, 'BLUESKY')
    monkeypatch.setenv('BLUESKY_APP_PASSWORD', 'your_bluesky_app_password')
    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
        preflight.enforce_required_secrets()
    assert exc.value.code == 1
    assert 'BLUESKY_APP_PASSWORD' in caplog.text
    assert 'your_bluesky_app_password' not in caplog.text


def test_enforce_passes_when_clean(monkeypatch):
    _enable(monkeypatch, 'BLUESKY')
    monkeypatch.setenv('BLUESKY_APP_PASSWORD', REAL)
    preflight.enforce_required_secrets()
