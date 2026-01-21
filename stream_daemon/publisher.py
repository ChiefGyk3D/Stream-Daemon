"""Social media publishing utilities for stream announcements.

The part where we spray your "I'm playing video games!" message across 4 different
platforms simultaneously, because apparently one wasn't enough. Gotta saturate that market.
"""

import logging
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from stream_daemon.ai import AIMessageGenerator
from stream_daemon.messaging import get_message_for_stream

logger = logging.getLogger(__name__)


def post_to_social_async(enabled_social: list,
                         ai_generator: AIMessageGenerator,
                         is_stream_start: bool,
                         platform_name: str,
                         username: str,
                         title: str,
                         url: str,
                         fallback_messages: List[str],
                         stream_data: Optional[dict] = None,
                         reply_to_ids: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
    """
    Post to all social platforms asynchronously using ThreadPoolExecutor.
    
    We use threads here because when you absolutely, positively need to tell
    4 different social networks AT THE SAME TIME that someone started playing Fortnite.
    Can't risk a 200ms delay. That's 200ms someone might miss the stream start. The horror.
    
    Args:
        enabled_social: List of enabled social platform instances
        ai_generator: AI message generator
        is_stream_start: True for stream start, False for end
        platform_name: Streaming platform name
        username: Streamer username
        title: Stream title
        url: Stream URL
        fallback_messages: Fallback messages if AI fails
        stream_data: Optional stream metadata for embeds
        reply_to_ids: Optional dict of {social_name: post_id} for threading
        
    Returns:
        Dict mapping social platform names to post IDs (or None if failed)
    """
    def post_to_single_platform(social):
        """Helper function to post to a single platform."""
        try:
            # Generate message with AI or fallback
            message = get_message_for_stream(
                ai_generator=ai_generator,
                is_stream_start=is_stream_start,
                platform_name=platform_name,
                username=username,
                title=title,
                url=url,
                social_platform_name=social.name.lower(),
                fallback_messages=fallback_messages
            )
            
            # Get reply_to_id if threading
            reply_to_id = None
            if reply_to_ids:
                reply_to_id = reply_to_ids.get(social.name)
            
            # Post to platform
            post_id = social.post(
                message,
                reply_to_id=reply_to_id,
                platform_name=platform_name,
                stream_data=stream_data
            )
            
            if post_id:
                logger.debug(f"  ✓ Posted to {social.name} (ID: {post_id})")
            else:
                logger.debug(f"  ✗ Failed to post to {social.name}")
                
            return (social.name, post_id)
        except Exception as e:
            logger.error(f"✗ Error posting to {social.name}: {e}")
            return (social.name, None)
    
    # Post to all platforms in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=len(enabled_social)) as executor:
        futures = [executor.submit(post_to_single_platform, social) for social in enabled_social]
        for future in as_completed(futures):
            social_name, post_id = future.result()
            results[social_name] = post_id
    
    return results
