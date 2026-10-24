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
from dataclasses import dataclass
from enum import Enum

from hypeman_social.config.secrets import get_secret as _library_get_secret

from .config import get_bool_config, get_config
from .secrets import (
    LLM_SECRETS,
    SOCIAL_SECRETS,
    backend_env_names,
    is_placeholder,
    known_env_name,
    secret_env_name,
)

logger = logging.getLogger(__name__)

_OK, _MISSING, _PLACEHOLDER = 'ok', 'missing', 'placeholder'


class Reason(Enum):
    MISSING = 'missing'
    PLACEHOLDER = 'placeholder'
    UNUSABLE = 'unusable'
    NEEDS_ONE_OF = 'needs_one_of'


# The only text a finding can log. Fixed strings, no formatting.
REASON_TEXT = {
    Reason.MISSING: "is required but is empty or unset",
    Reason.PLACEHOLDER: "is still a template placeholder; set the real value or clear it",
    Reason.UNUSABLE: "is required but is empty, unset, or a template placeholder",
    Reason.NEEDS_ONE_OF: "at least one of these must be set to a real value",
}

# Variable names that are not secrets themselves: the secrets-manager tokens.
_DOPPLER_TOKEN = 'DOPPLER_TOKEN'
_VAULT_TOKEN = 'SECRETS_VAULT_TOKEN'
_GEMINI_FALLBACK = 'GEMINI_API_KEY'


def _one_of_label(platform: str) -> str:
    return ' or '.join(secret_env_name(platform, k) for k in SOCIAL_SECRETS[platform]['one_of'])


# Every legal Finding.variable: constants from the tables, nothing else.
_ALLOWED_VARIABLES = frozenset(
    {_DOPPLER_TOKEN, _VAULT_TOKEN, _GEMINI_FALLBACK}
    | {known_env_name(p, k)
       for p, spec in SOCIAL_SECRETS.items() for keys in spec.values() for k in keys}
    | {known_env_name(p, k) for p, keys in LLM_SECRETS.items() for k in keys}
    | {_one_of_label(p) for p, spec in SOCIAL_SECRETS.items() if 'one_of' in spec}
)


@dataclass(frozen=True)
class Finding:
    """One start-up problem: a constant variable name and a fixed reason.

    Neither field is ever derived from a secret value or a secret lookup;
    the variable must come from the closed set built from the constant tables.
    """
    variable: str
    reason: Reason

    def __post_init__(self):
        if self.variable not in _ALLOWED_VARIABLES:
            raise ValueError("finding variable is not in the constant name set")
        if not isinstance(self.reason, Reason):
            raise TypeError("finding reason must be a Reason")


def _finding(platform: str, key: str, reason: Reason) -> Finding:
    return Finding(known_env_name(platform, key), reason)


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


def _check_social(platform: str, spec: dict) -> list[Finding]:
    found = []
    keys = spec.get('all', []) + spec.get('one_of', []) + spec.get('optional', [])
    states = {key: _status(platform, key) for key in keys}
    for key in keys:
        if states[key] == _PLACEHOLDER:
            found.append(_finding(platform, key, Reason.PLACEHOLDER))
    for key in spec.get('all', []):
        if states[key] == _MISSING:
            found.append(_finding(platform, key, Reason.MISSING))
    one_of = spec.get('one_of', [])
    if one_of and not any(states[k] == _OK for k in one_of) \
            and not any(states[k] == _PLACEHOLDER for k in one_of):
        found.append(Finding(_one_of_label(platform), Reason.NEEDS_ONE_OF))
    return found


def _llm_providers() -> list[str]:
    names = [get_config('LLM', 'provider', default='gemini') or '']
    names += (get_config('LLM', 'fallback_provider', default='') or '').split(',')
    return [n.strip().lower() for n in names if n.strip()]


def _check_gemini() -> list[Finding]:
    # hypeman-social reads LLM_GEMINI_API_KEY (or a secrets manager), then the
    # unprefixed GEMINI_API_KEY.
    state = _status('LLM', 'gemini_api_key')
    if state == _MISSING:
        raw = os.getenv('GEMINI_API_KEY')
        if raw and raw.strip():
            state = _PLACEHOLDER if is_placeholder(raw) else _OK
    if state == _OK:
        return []
    return [Finding(_GEMINI_FALLBACK, Reason.UNUSABLE)]


def check_required_secrets() -> list[Finding]:
    """Return one finding per problem; an empty list means start-up may go on."""
    found = []

    doppler = os.getenv('DOPPLER_TOKEN', '')
    if doppler.strip() and is_placeholder(doppler):
        found.append(Finding(_DOPPLER_TOKEN, Reason.PLACEHOLDER))
    if os.getenv('SECRETS_MANAGER', 'none').lower() == 'vault':
        if is_placeholder(os.getenv('SECRETS_VAULT_TOKEN')):
            found.append(Finding(_VAULT_TOKEN, Reason.UNUSABLE))
    if found:
        # A bad manager token would make every lookup below call out with it.
        return found

    for platform, spec in SOCIAL_SECRETS.items():
        if get_bool_config(platform, 'enable_posting', default=False):
            found += _check_social(platform, spec)

    if get_bool_config('LLM', 'enable', default=False) and 'gemini' in _llm_providers():
        found += _check_gemini()
    return found


def enforce_required_secrets() -> None:
    """Log every finding and exit 1 if any required secret is unusable."""
    failed = False
    for finding in check_required_secrets():
        logger.error("✗ %s: %s", finding.variable, REASON_TEXT[finding.reason])
        failed = True
    if not failed:
        return
    logger.error("   Refusing to start. Fix the variable(s) above in .env or your secrets manager.")
    sys.exit(1)
