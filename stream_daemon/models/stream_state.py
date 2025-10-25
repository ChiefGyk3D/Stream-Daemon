"""Stream state and status tracking models."""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamState(Enum):
    """States for stream lifecycle."""
    OFFLINE = "offline"
    LIVE = "live"


@dataclass
class StreamStatus:
    """Track the status of a streaming platform."""
    platform_name: str
    username: str
    state: StreamState = StreamState.OFFLINE
    title: Optional[str] = None
    stream_data: Optional[dict] = None  # Full stream data (title, viewers, thumbnail, etc.)
    went_live_at: Optional[datetime] = None
    last_check_live: bool = False
    consecutive_live_checks: int = 0
    consecutive_offline_checks: int = 0
    last_post_ids: Dict[str, str] = None  # social_platform_name -> post_id for threading
    
    def __post_init__(self):
        """Initialize mutable default values."""
        if self.last_post_ids is None:
            self.last_post_ids = {}
    
    @property
    def url(self) -> str:
        """Generate the stream URL based on platform and username."""
        try:
            if self.platform_name == 'Twitch':
                return f"https://twitch.tv/{self.username}"
            elif self.platform_name == 'YouTube':
                # YouTube URLs need the video ID, which we don't have here
                # Return channel URL as fallback
                return f"https://youtube.com/@{self.username}/live"
            elif self.platform_name == 'Kick':
                return f"https://kick.com/{self.username}"
            else:
                return f"https://{self.platform_name.lower()}.com/{self.username}"
        except Exception as e:
            logger.error(f"Error generating URL for {self.platform_name}/{self.username}: {e}")
            return f"https://{self.platform_name.lower()}.com/{self.username}"
    
    def update(self, is_live: bool, stream_data: Optional[dict] = None) -> bool:
        """
        Update status based on current check.
        Returns True if state actually changed (offline->live or live->offline).
        Uses debouncing to avoid false positives from API hiccups.
        
        Args:
            is_live: Whether stream is currently live
            stream_data: Dict with keys: title, viewer_count, thumbnail_url, game_name
        """
        try:
            if is_live:
                self.consecutive_live_checks += 1
                self.consecutive_offline_checks = 0
                
                # Extract title from stream_data for logging
                title = stream_data.get('title') if stream_data else None
                
                # Always update stream_data when live (even during debouncing)
                # This ensures already-live streams get their data when daemon starts
                if stream_data:
                    self.stream_data = stream_data
                
                # Require 2 consecutive live checks to confirm (debouncing)
                if self.state == StreamState.OFFLINE and self.consecutive_live_checks >= 2:
                    self.state = StreamState.LIVE
                    self.title = title
                    self.went_live_at = datetime.now()
                    self.last_post_ids = {}  # Reset threading for new stream
                    logger.info(f"🔴 {self.platform_name}/{self.username} went LIVE: {title}")
                    return True  # State changed!
                elif self.state == StreamState.LIVE:
                    # Update title if changed
                    if title and title != self.title:
                        logger.info(f"📝 {self.platform_name}/{self.username} updated title: {title}")
                        self.title = title
            else:
                self.consecutive_offline_checks += 1
                self.consecutive_live_checks = 0
                
                # Require 2 consecutive offline checks to confirm (debouncing)
                if self.state == StreamState.LIVE and self.consecutive_offline_checks >= 2:
                    self.state = StreamState.OFFLINE
                    duration = datetime.now() - self.went_live_at if self.went_live_at else None
                    logger.info(f"🔵 {self.platform_name}/{self.username} went OFFLINE (duration: {duration})")
                    self.title = None
                    self.stream_data = None
                    self.went_live_at = None
                    return True  # State changed!
        except Exception as e:
            logger.error(f"Error updating stream status for {self.platform_name}/{self.username}: {e}")
            return False
        
        return False  # No state change
