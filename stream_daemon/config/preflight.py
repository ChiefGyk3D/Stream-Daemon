# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Startup check for required secrets.

A feature the operator turned on needs its secret. If that secret is empty,
unset, or still the template placeholder, the daemon refuses to start and says
which variable to fix. The message names the variable and never its value.

hypeman-social reads the social and LLM secrets itself, with a placeholder
rule that only catches the upper-case YOUR_ prefix, so this check runs first
and applies stream_daemon.config.secrets.is_placeholder to the same lookups.
"""

import logging
import os
import sys

from hypeman_social.config.secrets import get_secret as _library_get_secret

from .config import get_bool_config, get_config
from .secrets import backend_env_names, is_placeholder, secret_env_name

logger = logging.getLogger(__name__)

# platform -> secret keys. 'all' must each be usable; 'one_of' needs at least
# one usable; 'optional' may be empty but never a placeholder. Any listed key
# that is set to a placeholder is an error, because the library would use it.
SOCIAL_SECRETS = {
    'Mastodon': {'all': ['access_token'], 'optional': ['client_id', 'client_secret']},
    'Bluesky': {'all': ['app_password']},
    'Discord': {'one_of': ['webhook_url', 'webhook_youtube', 'webhook_tiktok',
                           'webhook_twitch', 'webhook_kick']},
    'Matrix': {'one_of': ['password', 'access_token']},
}

_OK, _MISSING, _PLACEHOLDER = 'ok', 'missing', 'placeholder'


def _status(platform: str, key: str) -> str:
    raw = os.getenv(secret_env_name(platform, key))
    # Resolve through the same chain the library uses (Doppler, AWS, Vault,
    # env), so a value held in a secrets manager counts.
    value = _library_get_secret(platform, key, **backend_env_names(platform))
    if value is None:
        # The library already drops its own upper-case YOUR_ placeholders, so a
        # raw env value that is set but unusable is reported as a placeholder.
        return _PLACEHOLDER if (raw and raw.strip()) else _MISSING
    return _PLACEHOLDER if is_placeholder(value) else _OK


def _check_social(platform: str, spec: dict) -> list[str]:
    problems = []
    keys = spec.get('all', []) + spec.get('one_of', []) + spec.get('optional', [])
    states = {key: _status(platform, key) for key in keys}
    for key in keys:
        if states[key] == _PLACEHOLDER:
            problems.append(
                f"{secret_env_name(platform, key)} is still a template placeholder; "
                f"set the real value or clear it"
            )
    for key in spec.get('all', []):
        if states[key] == _MISSING:
            problems.append(f"{secret_env_name(platform, key)} is required for {platform} but is empty or unset")
    one_of = spec.get('one_of', [])
    if one_of and not any(states[k] == _OK for k in one_of) \
            and not any(states[k] == _PLACEHOLDER for k in one_of):
        names = ' or '.join(secret_env_name(platform, k) for k in one_of)
        problems.append(f"{platform} needs one of: {names}")
    return problems


def _llm_providers() -> list[str]:
    names = [get_config('LLM', 'provider', default='gemini') or '']
    names += (get_config('LLM', 'fallback_provider', default='') or '').split(',')
    return [n.strip().lower() for n in names if n.strip()]


def _check_gemini() -> list[str]:
    # hypeman-social reads LLM_GEMINI_API_KEY (or a secrets manager), then the
    # unprefixed GEMINI_API_KEY.
    state = _status('LLM', 'gemini_api_key')
    if state == _MISSING:
        raw = os.getenv('GEMINI_API_KEY')
        if raw and raw.strip():
            state = _PLACEHOLDER if is_placeholder(raw) else _OK
    if state == _OK:
        return []
    message = ("GEMINI_API_KEY is required for the Gemini LLM provider but is empty, "
               "unset, or a template placeholder")
    return [message]


def check_required_secrets() -> list[str]:
    """Return one message per problem; an empty list means start-up may go on."""
    problems = []

    doppler = os.getenv('DOPPLER_TOKEN', '')
    if doppler.strip() and is_placeholder(doppler):
        problems.append("DOPPLER_TOKEN is still a template placeholder; set the real token or remove it")
    if os.getenv('SECRETS_MANAGER', 'none').lower() == 'vault':
        token = os.getenv('SECRETS_VAULT_TOKEN')
        if is_placeholder(token):
            problems.append("SECRETS_VAULT_TOKEN is required when SECRETS_MANAGER=vault "
                            "but is empty, unset, or a template placeholder")
    if problems:
        # A bad manager token would make every lookup below call out with it.
        return problems

    for platform, spec in SOCIAL_SECRETS.items():
        if get_bool_config(platform, 'enable_posting', default=False):
            problems += _check_social(platform, spec)

    if get_bool_config('LLM', 'enable', default=False) and 'gemini' in _llm_providers():
        problems += _check_gemini()
    return problems


def enforce_required_secrets() -> None:
    """Log every problem and exit 1 if any required secret is unusable."""
    problems = check_required_secrets()
    if not problems:
        return
    for message in problems:
        logger.error(f"✗ {message}")
    logger.error("   Refusing to start. Fix the variable(s) above in .env or your secrets manager.")
    sys.exit(1)
