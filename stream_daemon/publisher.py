"""Social media publishing utilities for stream announcements."""

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
                         reply_to_ids: Optional[Dict[str, str]] = None,
                         stream_status=None) -> Dict[str, Optional[str]]:
    """
    Post to all social platforms asynchronously using ThreadPoolExecutor.
    
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
        reply_to_ids: Optional dict of {social_account_key: post_id} for threading
        stream_status: Optional StreamStatus object for social account filtering
        
    Returns:
        Dict mapping social account keys to post IDs (or None if failed)
    """
    def post_to_single_platform(social):
        """Helper function to post to a single platform."""
        try:
            # Check if this streamer should post to this social account
            if stream_status and not stream_status.should_post_to_account(social.name, social.account_id):
                logger.debug(f"  ⊘ Skipping {social.full_name} (not configured for {platform_name}/{username})")
                return (stream_status.get_social_account_key(social.name, social.account_id), None)
            
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
            
            # Get reply_to_id if threading (using account-specific key)
            reply_to_id = None
            if reply_to_ids:
                account_key = stream_status.get_social_account_key(social.name, social.account_id) if stream_status else social.name
                reply_to_id = reply_to_ids.get(account_key)
            
            # Post to platform
            post_id = social.post(
                message,
                reply_to_id=reply_to_id,
                platform_name=platform_name,
                stream_data=stream_data
            )
            
            if post_id:
                logger.debug(f"  ✓ Posted to {social.full_name} (ID: {post_id})")
            else:
                logger.debug(f"  ✗ Failed to post to {social.full_name}")
            
            # Return account-specific key for proper post ID tracking
            account_key = stream_status.get_social_account_key(social.name, social.account_id) if stream_status else social.name
            return (account_key, post_id)
        except Exception as e:
            logger.error(f"✗ Error posting to {social.full_name}: {e}")
            account_key = stream_status.get_social_account_key(social.name, social.account_id) if stream_status else social.name
            return (account_key, None)
    
    # Post to all platforms in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=len(enabled_social)) as executor:
        futures = [executor.submit(post_to_single_platform, social) for social in enabled_social]
        for future in as_completed(futures):
            account_key, post_id = future.result()
            results[account_key] = post_id
    
    return results
