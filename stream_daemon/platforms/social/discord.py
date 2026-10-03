# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Discord posting now lives in hypeman-social; this keeps the old import path
working. The library's default event kind is 'live', which is exactly what
stream-daemon announces.
"""

from hypeman_social.social.discord import DiscordPlatform

__all__ = ['DiscordPlatform']
