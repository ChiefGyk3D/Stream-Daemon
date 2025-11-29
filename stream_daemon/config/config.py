"""Configuration helper functions."""

import os
import logging

logger = logging.getLogger(__name__)


def get_config(section, key, default=None):
    """
    Get config from environment variables only.
    
    Args:
        section: Config section name (e.g., 'Twitch', 'Settings')
        key: Config key name (e.g., 'username', 'check_interval')
        default: Default value if not found
        
    Returns:
        Config value or default (also returns default if value is empty string)
    """
    try:
        env_key = f'{section.upper()}_{key.upper()}'
        value = os.getenv(env_key, default)
        # Return default if value is empty string
        return value if value else default
    except Exception as e:
        logger.error(f"Error getting config {section}.{key}: {e}")
        return default


def get_bool_config(section, key, default=False):
    """
    Get boolean config from environment variables.
    
    Args:
        section: Config section name
        key: Config key name
        default: Default boolean value
        
    Returns:
        Boolean config value
    """
    try:
        env_var = os.getenv(f'{section.upper()}_{key.upper()}')
        if env_var is not None:
            return env_var.lower() in ['true', '1', 't', 'y', 'yes']
        return default
    except Exception as e:
        logger.error(f"Error getting boolean config {section}.{key}: {e}")
        return default


def get_int_config(section, key, default=0):
    """
    Get integer config from environment variables.
    
    Args:
        section: Config section name
        key: Config key name
        default: Default integer value
        
    Returns:
        Integer config value
    """
    try:
        env_var = os.getenv(f'{section.upper()}_{key.upper()}')
        if env_var is not None:
            return int(env_var)
        return default
    except Exception as e:
        logger.error(f"Error getting integer config {section}.{key}: {e}")
        return default


def get_config_with_account(section, key, account_id='default', default=None):
    """
    Get config from environment variables with multi-account support.
    
    Tries account-specific variable first, falls back to default.
    Pattern: SECTION_ACCOUNTID_KEY or SECTION_KEY
    
    Args:
        section: Config section name (e.g., 'Discord', 'Mastodon')
        key: Config key name (e.g., 'webhook_url', 'api_base_url')
        account_id: Account identifier (e.g., 'gaming', 'personal', 'default')
        default: Default value if not found
        
    Returns:
        Config value or default
        
    Examples:
        get_config_with_account('Discord', 'webhook_url', 'gaming')
            → Tries DISCORD_GAMING_WEBHOOK_URL, then DISCORD_WEBHOOK_URL
        get_config_with_account('Mastodon', 'api_base_url', 'personal')
            → Tries MASTODON_PERSONAL_API_BASE_URL, then MASTODON_API_BASE_URL
    """
    try:
        # Try account-specific env var first (unless account_id is 'default')
        if account_id and account_id != 'default':
            account_key = f'{section.upper()}_{account_id.upper()}_{key.upper()}'
            value = os.getenv(account_key)
            if value:
                return value if value else default
        
        # Fall back to default env var (without account_id)
        default_key = f'{section.upper()}_{key.upper()}'
        value = os.getenv(default_key, default)
        return value if value else default
        
    except Exception as e:
        logger.error(f"Error getting config {section}.{key} for account {account_id}: {e}")
        return default


def get_bool_config_with_account(section, key, account_id='default', default=False):
    """
    Get boolean config with multi-account support.
    
    Args:
        section: Config section name
        key: Config key name
        account_id: Account identifier
        default: Default boolean value
        
    Returns:
        Boolean config value
    """
    try:
        # Try account-specific env var first
        if account_id and account_id != 'default':
            account_key = f'{section.upper()}_{account_id.upper()}_{key.upper()}'
            env_var = os.getenv(account_key)
            if env_var is not None:
                return env_var.lower() in ['true', '1', 't', 'y', 'yes']
        
        # Fall back to default
        default_key = f'{section.upper()}_{key.upper()}'
        env_var = os.getenv(default_key)
        if env_var is not None:
            return env_var.lower() in ['true', '1', 't', 'y', 'yes']
        
        return default
    except Exception as e:
        logger.error(f"Error getting boolean config {section}.{key} for account {account_id}: {e}")
        return default


def get_usernames(section, default=None):
    """
    Get list of usernames from environment variables.
    
    Supports both singular (USERNAME) and plural (USERNAMES) forms.
    Accepts comma-separated list for monitoring multiple users per platform.
    
    Args:
        section: Platform section name (e.g., 'Twitch', 'YouTube', 'Kick')
        default: Default value if not found (can be string or list)
        
    Returns:
        List of usernames (empty list if none found)
        
    Examples:
        TWITCH_USERNAME=user1                    → ['user1']
        TWITCH_USERNAMES=user1,user2,user3       → ['user1', 'user2', 'user3']
        YOUTUBE_USERNAME=@handle1, @handle2      → ['@handle1', '@handle2']
    """
    try:
        # Try plural form first (USERNAMES)
        plural_key = f'{section.upper()}_USERNAMES'
        usernames_str = os.getenv(plural_key)
        
        # Fall back to singular form (USERNAME) for backward compatibility
        if not usernames_str:
            singular_key = f'{section.upper()}_USERNAME'
            usernames_str = os.getenv(singular_key)
        
        # If still not found, use default
        if not usernames_str:
            if default is None:
                return []
            elif isinstance(default, list):
                return default
            else:
                return [default] if default else []
        
        # Split by comma and strip whitespace
        usernames = [u.strip() for u in usernames_str.split(',') if u.strip()]
        return usernames
        
    except Exception as e:
        logger.error(f"Error getting usernames for {section}: {e}")
        return [] if default is None else ([default] if isinstance(default, str) else default)
