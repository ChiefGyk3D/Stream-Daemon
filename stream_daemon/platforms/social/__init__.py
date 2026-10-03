"""
Social platform integrations for stream daemon.
"""

from .bluesky import BlueskyPlatform
from .discord import DiscordPlatform
from .mastodon import MastodonPlatform
from .matrix import MatrixPlatform

__all__ = [
    'BlueskyPlatform',
    'DiscordPlatform',
    'MastodonPlatform',
    'MatrixPlatform',
]
