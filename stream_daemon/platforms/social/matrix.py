# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Matrix posting now lives in hypeman-social; this keeps the old import path working."""

from hypeman_social.social.base import is_url_for_domain
from hypeman_social.social.matrix import MatrixPlatform


def _is_url_for_domain(url: str, domain: str) -> bool:
    """Kept for callers of the old private helper; use is_url_for_domain."""
    return is_url_for_domain(url, domain)


__all__ = ['MatrixPlatform', '_is_url_for_domain', 'is_url_for_domain']
