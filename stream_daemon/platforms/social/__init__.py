"""
Social platform integrations for stream daemon.
"""

from .mastodon import MastodonPlatform
from .bluesky import BlueskyPlatform
from .discord import DiscordPlatform
from .matrix import MatrixPlatform

__all__ = [
    'MastodonPlatform',
    'BlueskyPlatform',
    'DiscordPlatform',
    'MatrixPlatform',
]
