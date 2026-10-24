# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Secret management, now provided by hypeman-social.

Priority: Doppler -> AWS Secrets Manager -> Vault -> env/.env -> default.
A production secrets manager now genuinely overrides local .env values.
This module keeps the old import path working.
"""

import logging
import re

from hypeman_social.config.secrets import get_secret as _library_get_secret
from hypeman_social.config.secrets import (
    load_secrets_from_aws,
    load_secrets_from_doppler,
    load_secrets_from_vault,
)

logger = logging.getLogger(__name__)

# The one placeholder rule for this project. Case-insensitive. The library
# only rejects the upper-case 'YOUR_' prefix, so the lower-case your_* values
# in the example file used to be accepted as real secrets.
_PLACEHOLDER_PREFIXES = (
    'your_', 'your-', 'changeme', 'xxx', 'placeholder', 'dp.st.your',
)
_PLACEHOLDER_WORDS = ('example', 'placeholder')


def is_placeholder(value: str | None) -> bool:
    """True if VALUE is empty, unset, or an unedited template placeholder.

    Matches (case-insensitive): empty or whitespace, a value starting with
    your_, your-, changeme, xxx, placeholder or dp.st.your, the bare words
    example or placeholder, <...>, and any URL or path segment starting with
    your_ (the Discord webhook template).
    """
    if value is None:
        return True
    text = str(value).strip().lower()
    if not text or text in _PLACEHOLDER_WORDS:
        return True
    if text.startswith(_PLACEHOLDER_PREFIXES):
        return True
    if text.startswith('<') and text.endswith('>'):
        return True
    return any(seg.startswith('your_') for seg in re.split(r'[/:?&=]', text))


def secret_env_name(platform: str, key: str) -> str:
    """Name of the plain environment variable for a secret, e.g. MASTODON_ACCESS_TOKEN."""
    return f"{platform.upper()}_{key.upper()}"


def get_secret(platform: str, key: str, default: str | None = None, **backends) -> str | None:
    """hypeman-social's get_secret, plus this project's placeholder rule.

    A value that is_placeholder() is treated as not set: the default comes
    back and the log names the variable (never the value).
    """
    value = _library_get_secret(platform, key, default, **backends)
    if value is not None and value != default and is_placeholder(value):
        logger.warning(
            f"⚠ {secret_env_name(platform, key)} is empty or still a template "
            f"placeholder; treating it as not set"
        )
        return default
    return value


def backend_env_names(platform: str) -> dict[str, str]:
    """Name the environment variables that tell each secrets backend where
    PLATFORM's credentials live, for ``get_secret(..., **backend_env_names('Kick'))``.

    These are variable names, not credential values: ``SECRETS_AWS_KICK_SECRET_NAME``
    holds the name of the AWS secret, ``SECRETS_VAULT_KICK_SECRET_PATH`` the Vault
    path and ``SECRETS_DOPPLER_KICK_SECRET_NAME`` the name of the Doppler secret.
    Every platform follows the same pattern, so the platform modules derive the
    names here instead of each spelling out the same three literals.
    """
    name = platform.upper()
    return {
        'secret_name_env': f'SECRETS_AWS_{name}_SECRET_NAME',
        'secret_path_env': f'SECRETS_VAULT_{name}_SECRET_PATH',
        'doppler_secret_env': f'SECRETS_DOPPLER_{name}_SECRET_NAME',
    }


__all__ = [
    'backend_env_names',
    'get_secret',
    'is_placeholder',
    'load_secrets_from_aws',
    'load_secrets_from_doppler',
    'load_secrets_from_vault',
    'secret_env_name',
]
