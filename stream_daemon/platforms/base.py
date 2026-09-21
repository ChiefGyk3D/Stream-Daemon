"""
Base classes for platform integrations.

StreamingPlatform (Twitch/YouTube/Kick monitoring) is stream-daemon's own.
SocialPlatform now comes from hypeman-social, shared with the other daemons.
"""

import logging

from hypeman_social.social.base import SocialPlatform

logger = logging.getLogger(__name__)

__all__ = ['SocialPlatform', 'StreamingPlatform']


class StreamingPlatform:
    """Base class for streaming platforms like Twitch, YouTube, Kick."""
    
    def __init__(self, name: str):
        """
        Initialize streaming platform.
        
        Args:
            name: Platform name (e.g., 'Twitch', 'YouTube')
        """
        self.name = name
        self.enabled = False
    
    def is_live(self, username: str) -> tuple[bool, dict | None]:
        """
        Check if user is live.
        
        Args:
            username: Username/channel to check
            
        Returns:
            Tuple of (is_live, stream_data) where stream_data contains:
            - title: Stream title
            - viewer_count: Current viewer count
            - thumbnail_url: Thumbnail URL
            - game_name: Game/category name
        """
        raise NotImplementedError(f"{self.name}.is_live() must be implemented")
    
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            bool: True if authentication successful
        """
        raise NotImplementedError(f"{self.name}.authenticate() must be implemented")
