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
        Config value or default
    """
    try:
        env_key = f'{section.upper()}_{key.upper()}'
        return os.getenv(env_key, default)
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
