# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Bluesky posting now lives in hypeman-social; this keeps the old import path working."""

from hypeman_social.social.bluesky import BlueskyPlatform

__all__ = ['BlueskyPlatform']
