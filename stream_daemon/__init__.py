"""
Stream Daemon - Universal streaming-to-social bridge.

This package provides modular components for monitoring streaming platforms
(Twitch, YouTube, Kick) and posting to social media (Mastodon, Bluesky, Discord, Matrix).
"""

__version__ = '2.0.0'
__author__ = 'ChiefGyk3D'

# Core modules
from . import config
from . import models  
from . import ai
from . import utils
from . import platforms

# Commonly used exports
from .config import get_config, get_bool_config, get_int_config, get_secret
from .models import StreamState, StreamStatus
from .ai import AIMessageGenerator
from .utils import parse_sectioned_message_file

__all__ = [
    # Modules
    'config',
    'models',
    'ai',
    'utils',
    'platforms',
    # Functions
    'get_config',
    'get_bool_config',
    'get_int_config',
    'get_secret',
    'parse_sectioned_message_file',
    # Classes
    'StreamState',
    'StreamStatus',
    'AIMessageGenerator',
]
