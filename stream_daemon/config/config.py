# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Configuration access, now provided by hypeman-social.

Same lookup rules as before: Doppler (if DOPPLER_TOKEN is set), then simple
env keys (CHECK_INTERVAL), then sectioned keys (SETTINGS_CHECK_INTERVAL),
then the default. This module keeps the old import path working.
"""

from hypeman_social.config import (
    get_bool_config,
    get_config,
    get_float_config,
    get_int_config,
    get_usernames,
    load_config,
)

__all__ = [
    'get_bool_config',
    'get_config',
    'get_float_config',
    'get_int_config',
    'get_usernames',
    'load_config',
]
