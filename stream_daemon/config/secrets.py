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

__all__ = [
    'get_secret',
    'load_secrets_from_aws',
    'load_secrets_from_doppler',
    'load_secrets_from_vault',
]
