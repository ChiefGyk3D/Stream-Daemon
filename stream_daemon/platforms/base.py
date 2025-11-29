"""Base classes for platform integrations."""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


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
    
    def is_live(self, username: str) -> Tuple[bool, Optional[dict]]:
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


class SocialPlatform:
    """Base class for social media platforms like Mastodon, Bluesky, Discord."""
    
    def __init__(self, name: str, account_id: str = 'default'):
        """
        Initialize social platform.
        
        Args:
            name: Platform name (e.g., 'Mastodon', 'Bluesky')
            account_id: Unique identifier for this account (e.g., 'personal', 'gaming', 'work')
        """
        self.name = name
        self.account_id = account_id
        self.enabled = False
    
    @property
    def full_name(self) -> str:
        """Get full name including account ID."""
        if self.account_id == 'default':
            return self.name
        return f"{self.name}:{self.account_id}"
    
    def post(self, message: str, reply_to_id: Optional[str] = None, 
             platform_name: Optional[str] = None, 
             stream_data: Optional[dict] = None) -> Optional[str]:
        """
        Post a message to the social platform.
        
        Args:
            message: Message content to post
            reply_to_id: ID of post to reply to (for threading)
            platform_name: Name of streaming platform (for platform-specific formatting)
            stream_data: Stream metadata (title, viewers, thumbnail, etc.)
            
        Returns:
            str: Post ID if successful, None otherwise
        """
        raise NotImplementedError(f"{self.name}.post() must be implemented")
    
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            bool: True if authentication successful
        """
        raise NotImplementedError(f"{self.name}.authenticate() must be implemented")
