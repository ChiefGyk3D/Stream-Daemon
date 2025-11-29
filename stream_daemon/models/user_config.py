"""User-to-social-account mapping configuration models."""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)


@dataclass
class SocialAccountConfig:
    """Configuration for a social media account."""
    platform: str  # 'mastodon', 'bluesky', 'discord', 'matrix'
    account_id: str  # Unique identifier for this account (e.g., 'personal', 'gaming', 'work')
    
    def __str__(self):
        return f"{self.platform}:{self.account_id}"
    
    def __hash__(self):
        return hash((self.platform, self.account_id))
    
    def __eq__(self, other):
        if not isinstance(other, SocialAccountConfig):
            return False
        return self.platform == other.platform and self.account_id == other.account_id


@dataclass
class StreamerConfig:
    """Configuration for a single streamer."""
    platform: str  # 'Twitch', 'YouTube', 'Kick'
    username: str
    social_accounts: List[SocialAccountConfig] = field(default_factory=list)
    
    @property
    def key(self) -> str:
        """Unique identifier for this streamer."""
        return f"{self.platform}/{self.username}"
    
    def __str__(self):
        accounts_str = ', '.join([str(acc) for acc in self.social_accounts])
        return f"{self.key} → [{accounts_str}]"


@dataclass
class MultiUserConfig:
    """
    Complete multi-user configuration supporting:
    - Multiple streaming users per platform
    - Multiple social accounts per platform
    - Per-user social account routing
    """
    streamers: List[StreamerConfig] = field(default_factory=list)
    
    def add_streamer(self, platform: str, username: str, 
                     social_accounts: Optional[List[SocialAccountConfig]] = None) -> StreamerConfig:
        """Add a streamer configuration."""
        config = StreamerConfig(
            platform=platform,
            username=username,
            social_accounts=social_accounts or []
        )
        self.streamers.append(config)
        return config
    
    def get_streamer(self, platform: str, username: str) -> Optional[StreamerConfig]:
        """Get a specific streamer's configuration."""
        for streamer in self.streamers:
            if streamer.platform == platform and streamer.username == username:
                return streamer
        return None
    
    def get_social_accounts_for_streamer(self, platform: str, username: str) -> List[SocialAccountConfig]:
        """Get list of social accounts that should receive posts for this streamer."""
        streamer = self.get_streamer(platform, username)
        if streamer:
            return streamer.social_accounts
        return []
    
    def get_all_social_accounts(self) -> Set[SocialAccountConfig]:
        """Get set of all unique social accounts across all streamers."""
        accounts = set()
        for streamer in self.streamers:
            accounts.update(streamer.social_accounts)
        return accounts
    
    def get_streamers_by_platform(self, platform: str) -> List[StreamerConfig]:
        """Get all streamers for a specific streaming platform."""
        return [s for s in self.streamers if s.platform == platform]
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        Returns True if valid, False otherwise.
        Logs warnings for issues.
        """
        if not self.streamers:
            logger.error("No streamers configured in MultiUserConfig")
            return False
        
        # Check for duplicate streamer keys
        keys = [s.key for s in self.streamers]
        if len(keys) != len(set(keys)):
            logger.error("Duplicate streamer configurations found")
            return False
        
        # Warn about streamers with no social accounts
        for streamer in self.streamers:
            if not streamer.social_accounts:
                logger.warning(f"Streamer {streamer.key} has no social accounts configured")
        
        return True
    
    @classmethod
    def from_env_simple(cls, streaming_platforms: List, social_platforms: List) -> 'MultiUserConfig':
        """
        Create config from simple environment variables (backward compatible).
        
        Uses existing USERNAME/USERNAMES env vars and posts to ALL enabled social platforms.
        This maintains backward compatibility with the original single-user setup.
        
        Args:
            streaming_platforms: List of authenticated streaming platform objects
            social_platforms: List of authenticated social platform objects
        """
        from stream_daemon.config import get_usernames
        
        config = cls()
        
        # Get all enabled social accounts (one per platform in simple mode)
        social_accounts = [
            SocialAccountConfig(platform=p.name.lower(), account_id='default')
            for p in social_platforms
        ]
        
        # Create streamer configs using existing USERNAME/USERNAMES env vars
        for platform in streaming_platforms:
            usernames = get_usernames(platform.name)
            for username in usernames:
                config.add_streamer(
                    platform=platform.name,
                    username=username,
                    social_accounts=social_accounts  # All streamers post to all platforms
                )
        
        return config
    
    @classmethod
    def from_env_advanced(cls) -> Optional['MultiUserConfig']:
        """
        Create config from advanced environment variable format.
        
        Format: MULTI_USER_CONFIG as JSON string or file path
        
        JSON structure:
        {
            "streamers": [
                {
                    "platform": "Twitch",
                    "username": "user1",
                    "social_accounts": [
                        {"platform": "discord", "account_id": "gaming"},
                        {"platform": "mastodon", "account_id": "personal"}
                    ]
                },
                {
                    "platform": "Twitch", 
                    "username": "user2",
                    "social_accounts": [
                        {"platform": "discord", "account_id": "gaming"},
                        {"platform": "bluesky", "account_id": "tech"}
                    ]
                }
            ]
        }
        
        Returns None if MULTI_USER_CONFIG is not set.
        """
        import os
        
        multi_user_config_str = os.getenv('MULTI_USER_CONFIG')
        if not multi_user_config_str:
            return None
        
        try:
            # Check if it's a file path
            if multi_user_config_str.endswith('.json') and os.path.isfile(multi_user_config_str):
                logger.info(f"Loading multi-user config from file: {multi_user_config_str}")
                with open(multi_user_config_str, 'r') as f:
                    data = json.load(f)
            else:
                # Parse as JSON string
                data = json.loads(multi_user_config_str)
            
            config = cls()
            
            for streamer_data in data.get('streamers', []):
                platform = streamer_data.get('platform')
                username = streamer_data.get('username')
                
                if not platform or not username:
                    logger.warning(f"Skipping invalid streamer config: {streamer_data}")
                    continue
                
                social_accounts = []
                for acc_data in streamer_data.get('social_accounts', []):
                    social_platform = acc_data.get('platform')
                    account_id = acc_data.get('account_id', 'default')
                    
                    if social_platform:
                        social_accounts.append(
                            SocialAccountConfig(platform=social_platform, account_id=account_id)
                        )
                
                config.add_streamer(platform, username, social_accounts)
            
            if config.validate():
                logger.info(f"Loaded advanced multi-user config with {len(config.streamers)} streamers")
                return config
            else:
                logger.error("Invalid multi-user config, falling back to simple mode")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MULTI_USER_CONFIG JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading multi-user config: {e}")
            return None
    
    @classmethod
    def load(cls, streaming_platforms: List, social_platforms: List) -> 'MultiUserConfig':
        """
        Load multi-user configuration with fallback.
        
        Priority:
        1. MULTI_USER_CONFIG (advanced JSON mode) if set
        2. Simple mode using existing USERNAME/USERNAMES env vars (backward compatible)
        
        Args:
            streaming_platforms: List of authenticated streaming platform objects
            social_platforms: List of authenticated social platform objects
        """
        # Try advanced mode first
        config = cls.from_env_advanced()
        if config:
            logger.info("✓ Using advanced multi-user configuration mode")
            return config
        
        # Fall back to simple mode (backward compatible)
        logger.info("✓ Using simple configuration mode (backward compatible)")
        config = cls.from_env_simple(streaming_platforms, social_platforms)
        
        if not config.validate():
            raise ValueError("Failed to create valid multi-user configuration")
        
        return config
