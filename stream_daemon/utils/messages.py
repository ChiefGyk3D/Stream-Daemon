"""Message file parsing utilities."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def parse_sectioned_message_file(filepath: str) -> Dict[str, List[str]]:
    """
    Parse a message file with platform-specific sections.
    
    Format:
        [DEFAULT]
        message 1
        message 2
        
        [TWITCH]
        twitch message 1
        twitch message 2
        
        [YOUTUBE]
        youtube message 1
    
    Args:
        filepath: Path to the message file
        
    Returns:
        Dict mapping platform name (or 'DEFAULT') to list of messages
    """
    sections = {}
    current_section = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Check if this is a section header
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].upper()
                    if current_section not in sections:
                        sections[current_section] = []
                    continue
                
                # Add message to current section
                if current_section:
                    sections[current_section].append(line)
        
        logger.debug(f"Parsed message file {filepath}: {len(sections)} sections")
        return sections
    
    except FileNotFoundError:
        logger.warning(f"⚠ Message file not found: {filepath}")
        return {}
    except Exception as e:
        logger.error(f"Error parsing message file {filepath}: {e}")
        return {}
