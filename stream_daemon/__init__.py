"""
Stream Daemon - Universal streaming-to-social bridge.

This package provides modular components for monitoring streaming platforms
(Twitch, YouTube, Kick) and posting to social media (Mastodon, Bluesky, Discord, Matrix).

Or in simpler terms: We watch other people play games, then tell the internet about it.
With modules. And components. And clean architecture. Because we're professionals.

This is version 2.0.0. There was a version 1.0.0. We learned from our mistakes.
Now we have MORE modules and BETTER architecture to do the exact same thing.
Progress!
"""

__version__ = '2.0.0'
__author__ = 'ChiefGyk3D'

# Core modules
from . import ai, config, models, platforms, utils
from .ai import AIMessageGenerator

# Commonly used exports
from .config import get_bool_config, get_config, get_int_config, get_secret
from .models import StreamState, StreamStatus
from .utils import parse_sectioned_message_file

__all__ = [
    'AIMessageGenerator',
    'StreamState',
    'StreamStatus',
    'ai',
    'config',
    'get_bool_config',
    'get_config',
    'get_int_config',
    'get_secret',
    'models',
    'parse_sectioned_message_file',
    'platforms',
    'utils',
]
