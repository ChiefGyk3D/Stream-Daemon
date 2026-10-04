# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Secret management, now provided by hypeman-social.

Priority: Doppler -> AWS Secrets Manager -> Vault -> env/.env -> default.
A production secrets manager now genuinely overrides local .env values.
This module keeps the old import path working.
"""

from hypeman_social.config.secrets import (
    get_secret,
    load_secrets_from_aws,
    load_secrets_from_doppler,
    load_secrets_from_vault,
)


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
    'load_secrets_from_aws',
    'load_secrets_from_doppler',
    'load_secrets_from_vault',
]
