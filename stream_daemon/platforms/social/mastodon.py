# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Mastodon posting now lives in hypeman-social; this keeps the old import path working."""

from hypeman_social.social.base import SocialPlatform
from hypeman_social.social.mastodon import MastodonPlatform

__all__ = ['MastodonPlatform', 'SocialPlatform']
