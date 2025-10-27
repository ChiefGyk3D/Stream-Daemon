"""Message generation utilities for stream announcements."""

import logging
import random
from typing import List

from stream_daemon.ai import AIMessageGenerator

logger = logging.getLogger(__name__)


def get_message_for_stream(ai_generator: AIMessageGenerator,
                           is_stream_start: bool,
                           platform_name: str,
                           username: str,
                           title: str,
                           url: str,
                           social_platform_name: str,
                           fallback_messages: List[str]) -> str:
    """
    Get message for stream announcement, using AI if enabled, otherwise fallback.
    
    Args:
        ai_generator: AI message generator instance
        is_stream_start: True for start, False for end
        platform_name: Streaming platform (Twitch, YouTube, Kick)
        username: Streamer username
        title: Stream title
        url: Stream URL (for start messages)
        social_platform_name: Social platform name (bluesky, mastodon, discord, matrix)
        fallback_messages: List of template messages to use if AI disabled
    
    Returns:
        Formatted message ready to post
    """
    # Try AI generation if enabled
    if ai_generator.enabled:
        try:
            if is_stream_start:
                ai_message = ai_generator.generate_stream_start_message(
                    platform_name=platform_name,
                    username=username,
                    title=title,
                    url=url,
                    social_platform=social_platform_name
                )
                if ai_message:
                    return ai_message
                logger.warning("⚠ AI generation returned None, using fallback message")
            else:
                ai_message = ai_generator.generate_stream_end_message(
                    platform_name=platform_name,
                    username=username,
                    title=title,
                    social_platform=social_platform_name
                )
                if ai_message:
                    return ai_message
                logger.warning("⚠ AI generation returned None, using fallback message")
        except Exception as e:
            logger.error(f"✗ AI message generation failed: {e}, using fallback")
    
    # Fallback to traditional messages
    if not fallback_messages:
        logger.error(f"✗ No fallback messages available for {platform_name}")
        return f"🎮 {username} is {'now live' if is_stream_start else 'done streaming'} on {platform_name}! {title}"
    
    # Pick random fallback and format it
    message = random.choice(fallback_messages).format(
        stream_title=title,
        username=username,
        platform=platform_name
    )
    return message
