"""
Stream Daemon - Universal streaming-to-social bridge
Monitors streaming platforms and posts to social media
Configuration via .env files and environment variables only
"""

import time
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict

# Import from modularized package
from stream_daemon.config import get_config, get_bool_config, get_int_config
from stream_daemon.models import StreamState, StreamStatus
from stream_daemon.ai import AIMessageGenerator
from stream_daemon.utils import parse_sectioned_message_file
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform
from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform
from stream_daemon.publisher import post_to_social_async

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()
logger.info("Environment variables loaded")


# ===========================================
# MAIN APPLICATION
# ===========================================

def main():
    """Main application loop with improved state tracking and per-platform posting."""
    
    logger.info("="*60)
    logger.info("🚀 Stream Daemon Starting...")
    logger.info("="*60)
    
    # Initialize streaming platforms
    streaming_platforms = [
        TwitchPlatform(),
        YouTubePlatform(),
        KickPlatform()
    ]
    
    enabled_streaming = []
    for platform in streaming_platforms:
        if platform.authenticate():
            enabled_streaming.append(platform)
    
    if not enabled_streaming:
        logger.error("✗ No streaming platforms configured!")
        logger.error("   Enable at least one: Twitch, YouTube, or Kick")
        sys.exit(1)
    
    # Initialize social platforms
    social_platforms = [
        MastodonPlatform(),
        BlueskyPlatform(),
        DiscordPlatform(),
        MatrixPlatform()
    ]
    
    enabled_social = []
    for platform in social_platforms:
        if platform.authenticate():
            enabled_social.append(platform)
    
    if not enabled_social:
        logger.error("✗ No social platforms configured!")
        logger.error("   Enable at least one: Mastodon, Bluesky, Discord, or Matrix")
        sys.exit(1)
    
    # Initialize AI message generator (optional)
    ai_generator = AIMessageGenerator()
    ai_generator.authenticate()  # Will log if enabled/disabled
    
    # Load messages from consolidated files with platform sections
    messages_file = get_config('Messages', 'messages_file', default='messages.txt')
    end_messages_file = get_config('Messages', 'end_messages_file', default='end_messages.txt')
    
    # Load new threading mode configurations
    live_threading_mode = get_config('Messages', 'live_threading_mode', default='separate').lower()
    end_threading_mode = get_config('Messages', 'end_threading_mode', default='thread').lower()
    
    # Backwards compatibility with old config
    post_end_stream_message = get_bool_config('Messages', 'post_end_stream_message', default=True)
    if not post_end_stream_message:
        end_threading_mode = 'disabled'
    
    # Validate threading modes
    valid_live_modes = ['separate', 'thread', 'combined']
    valid_end_modes = ['disabled', 'separate', 'thread', 'combined', 'single_when_all_end']
    
    if live_threading_mode not in valid_live_modes:
        logger.warning(f"⚠ Invalid LIVE_THREADING_MODE '{live_threading_mode}', using 'separate'")
        live_threading_mode = 'separate'
    
    if end_threading_mode not in valid_end_modes:
        logger.warning(f"⚠ Invalid END_THREADING_MODE '{end_threading_mode}', using 'thread'")
        end_threading_mode = 'thread'
    
    logger.info(f"📋 Live posting mode: {live_threading_mode}")
    logger.info(f"📋 End posting mode: {end_threading_mode}")
    
    use_platform_specific = get_bool_config('Messages', 'use_platform_specific_messages', default=True)
    
    # Parse message files
    logger.info(f"📝 Loading messages from {messages_file} and {end_messages_file}")
    live_sections = parse_sectioned_message_file(messages_file)
    end_sections = parse_sectioned_message_file(end_messages_file)
    
    if not live_sections:
        logger.error(f"✗ Failed to load messages from {messages_file}")
        sys.exit(1)
    
    # Check if we have DEFAULT section
    has_default = 'DEFAULT' in live_sections
    has_end_default = 'DEFAULT' in end_sections
    
    # Build messages dict for each platform
    messages = {}  # platform_name -> list of messages
    end_messages = {}  # platform_name -> list of end messages
    
    for platform in enabled_streaming:
        platform_name = platform.name.upper()
        
        # Live messages
        if use_platform_specific and platform_name in live_sections:
            messages[platform.name] = live_sections[platform_name]
            logger.info(f"  • Loaded {len(messages[platform.name])} platform-specific live messages for {platform.name}")
        elif has_default:
            messages[platform.name] = live_sections['DEFAULT']
            logger.info(f"  • Using {len(messages[platform.name])} DEFAULT live messages for {platform.name}")
        else:
            logger.error(f"✗ No messages found for {platform.name} (no platform section and no DEFAULT)")
            sys.exit(1)
        
        # End messages (optional)
        if use_platform_specific and platform_name in end_sections:
            end_messages[platform.name] = end_sections[platform_name]
            logger.info(f"  • Loaded {len(end_messages[platform.name])} platform-specific end messages for {platform.name}")
        elif has_end_default:
            end_messages[platform.name] = end_sections['DEFAULT']
            logger.info(f"  • Using {len(end_messages[platform.name])} DEFAULT end messages for {platform.name}")
        else:
            end_messages[platform.name] = []
            logger.debug(f"  • No end messages for {platform.name} (optional)")
    
    # Get usernames for each platform and create StreamStatus trackers
    stream_statuses: Dict[str, StreamStatus] = {}
    for platform in enabled_streaming:
        username = get_config(platform.name, 'username')
        if username:
            status = StreamStatus(
                platform_name=platform.name,
                username=username
            )
            stream_statuses[platform.name] = status
            logger.info(f"  • Monitoring {platform.name}/{username}")
        else:
            logger.warning(f"⚠ No username configured for {platform.name}, skipping")
    
    if not stream_statuses:
        logger.error("✗ No usernames configured for any streaming platforms!")
        sys.exit(1)
    
    # Settings
    post_interval = get_int_config('Settings', 'post_interval', default=1)
    check_interval = get_int_config('Settings', 'check_interval', default=5)
    
    # Track platforms that went live in this session (for single_when_all_end mode)
    platforms_that_went_live = set()
    last_live_post_ids = {}  # For combined/thread modes: social_platform -> last_post_id
    
    logger.info("="*60)
    logger.info(f"📺 Monitoring: {', '.join([f'{s.platform_name}/{s.username}' for s in stream_statuses.values()])}")
    logger.info(f"📱 Posting to: {', '.join([p.name for p in enabled_social])}")
    logger.info(f"⏰ Check: {check_interval}min (offline) / {post_interval}min (live)")
    logger.info("="*60)
    
    # Main loop with improved state tracking
    while True:
        try:
            logger.info("🔍 Checking streams...")
            
            # Collect platforms that just went live or offline in this check cycle
            platforms_went_live = []
            platforms_went_offline = []
            
            # Check all streaming platforms
            for platform in enabled_streaming:
                status = stream_statuses.get(platform.name)
                if not status:
                    continue
                
                # Check if stream is live (returns is_live bool and stream_data dict)
                is_live, stream_data = platform.is_live(status.username)
                
                # Update status and check if state changed
                state_changed = status.update(is_live, stream_data)
                
                if state_changed:
                    if status.state == StreamState.LIVE:
                        platforms_went_live.append(status)
                        platforms_that_went_live.add(status.platform_name)
                    elif status.state == StreamState.OFFLINE:
                        platforms_went_offline.append(status)
                else:
                    # No state change - just log current status
                    if status.state == StreamState.LIVE:
                        logger.debug(f"  {status.platform_name}/{status.username}: Still live ({status.consecutive_live_checks} checks)")
                        
                        # Update Discord embeds with fresh stream data (viewer count, thumbnail)
                        for social in enabled_social:
                            if isinstance(social, DiscordPlatform) and status.stream_data:
                                if social.update_stream(status.platform_name, status.stream_data, status.url):
                                    logger.info(f"  ✓ Updated Discord embed for {status.platform_name} (viewers: {status.stream_data.get('viewer_count', 'N/A')})")
                    else:
                        logger.debug(f"  {status.platform_name}/{status.username}: Still offline ({status.consecutive_offline_checks} checks)")
            
            # ================================================================
            # HANDLE PLATFORMS THAT WENT LIVE
            # ================================================================
            if platforms_went_live:
                if live_threading_mode == 'combined':
                    # COMBINED MODE: Single post listing all platforms
                    platform_names = ', '.join([s.platform_name for s in platforms_went_live])
                    titles = ' | '.join([f"{s.platform_name}: {s.title}" for s in platforms_went_live])
                    
                    # Use first platform's info for URL generation
                    first_platform = platforms_went_live[0]
                    platform_messages = messages.get(first_platform.platform_name, [])
                    
                    logger.info(f"📢 Posting combined 'LIVE' announcement for {platform_names}")
                    
                    # Post to all platforms asynchronously
                    post_results = post_to_social_async(
                        enabled_social=enabled_social,
                        ai_generator=ai_generator,
                        is_stream_start=True,
                        platform_name=platform_names,
                        username=first_platform.username,
                        title=titles,
                        url=first_platform.url or '',
                        fallback_messages=platform_messages,
                        stream_data=first_platform.stream_data,
                        reply_to_ids=None
                    )
                    
                    # Process results
                    posted_count = 0
                    for social_name, post_id in post_results.items():
                        if post_id:
                            posted_count += 1
                            last_live_post_ids[social_name] = post_id
                            # Save post ID to each platform status for potential end threading
                            for status in platforms_went_live:
                                status.last_post_ids[social_name] = post_id
                    
                    if posted_count > 0:
                        logger.info(f"✓ Posted to {posted_count}/{len(enabled_social)} platform(s)")
                    else:
                        logger.warning(f"⚠ Failed to post to any platforms")
                
                else:
                    # SEPARATE or THREAD MODE: Post for each platform
                    for idx, status in enumerate(platforms_went_live):
                        platform_messages = messages.get(status.platform_name, [])
                        if not platform_messages:
                            logger.error(f"✗ No messages configured for {status.platform_name}")
                            continue
                        
                        logger.info(f"📢 Posting 'LIVE' announcement for {status.platform_name}/{status.username}")
                        
                        # Determine reply_to_ids for threading
                        reply_to_ids = None
                        if live_threading_mode == 'thread' and idx > 0:
                            # Thread to previous posts
                            reply_to_ids = last_live_post_ids.copy()
                        
                        # Add delay between streaming platforms to prevent API burst
                        # Each platform posts to 4 social platforms in parallel
                        # 3-5 second delay keeps us under Gemini's burst limit
                        if idx > 0:
                            time.sleep(4)  # Wait 4 seconds between each streaming platform
                        
                        # Post to all platforms asynchronously
                        post_results = post_to_social_async(
                            enabled_social=enabled_social,
                            ai_generator=ai_generator,
                            is_stream_start=True,
                            platform_name=status.platform_name,
                            username=status.username,
                            title=status.title,
                            url=status.url or '',
                            fallback_messages=platform_messages,
                            stream_data=status.stream_data,
                            reply_to_ids=reply_to_ids
                        )
                        
                        # Process results
                        posted_count = 0
                        for social_name, post_id in post_results.items():
                            if post_id:
                                posted_count += 1
                                last_live_post_ids[social_name] = post_id
                                status.last_post_ids[social_name] = post_id
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted to {posted_count}/{len(enabled_social)} platform(s)")
                        else:
                            logger.warning(f"⚠ Failed to post to any platforms")
            
            # ================================================================
            # HANDLE PLATFORMS THAT WENT OFFLINE
            # ================================================================
            if platforms_went_offline and end_threading_mode != 'disabled':
                
                if end_threading_mode == 'single_when_all_end':
                    # Check if ALL platforms that went live are now offline
                    all_ended = all(
                        stream_statuses[pname].state == StreamState.OFFLINE 
                        for pname in platforms_that_went_live
                    )
                    
                    if all_ended and platforms_that_went_live:
                        # Post single "all streams ended" message
                        platform_names = ', '.join(sorted(platforms_that_went_live))
                        
                        # Use first platform's end messages as template
                        first_platform_name = next(iter(platforms_that_went_live))
                        first_status = stream_statuses[first_platform_name]
                        platform_end_messages = end_messages.get(first_platform_name, [])
                        
                        if platform_end_messages:
                            logger.info(f"📢 Posting final 'ALL STREAMS ENDED' announcement for {platform_names}")
                            
                            # Handle Discord separately (update embeds)
                            discord_count = 0
                            for social in enabled_social:
                                if isinstance(social, DiscordPlatform):
                                    for pname in platforms_that_went_live:
                                        status = stream_statuses[pname]
                                        if social.end_stream(status.platform_name, status.stream_data or {}, status.url):
                                            discord_count += 1
                                            logger.debug(f"  ✓ Updated Discord embed for {status.platform_name}")
                            
                            # Post to non-Discord platforms asynchronously
                            non_discord_social = [s for s in enabled_social if not isinstance(s, DiscordPlatform)]
                            if non_discord_social:
                                post_results = post_to_social_async(
                                    enabled_social=non_discord_social,
                                    ai_generator=ai_generator,
                                    is_stream_start=False,
                                    platform_name=platform_names,
                                    username=first_status.username,
                                    title=first_status.title,
                                    url='',
                                    fallback_messages=platform_end_messages,
                                    stream_data=None,
                                    reply_to_ids=last_live_post_ids.copy()
                                )
                                
                                posted_count = discord_count + sum(1 for pid in post_results.values() if pid)
                            else:
                                posted_count = discord_count
                            
                            if posted_count > 0:
                                logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
                            
                            # Clear tracking since all streams ended
                            platforms_that_went_live.clear()
                            last_live_post_ids.clear()
                    else:
                        logger.debug(f"  Waiting for all streams to end (mode: single_when_all_end)")
                
                elif end_threading_mode == 'combined':
                    # COMBINED MODE: Single post for all platforms that ended
                    platform_names = ', '.join([s.platform_name for s in platforms_went_offline])
                    
                    # Use first platform's end messages
                    first_status = platforms_went_offline[0]
                    platform_end_messages = end_messages.get(first_status.platform_name, [])
                    
                    if platform_end_messages:
                        logger.info(f"📢 Posting combined 'OFFLINE' announcement for {platform_names}")
                        
                        # Handle Discord separately (update embeds)
                        discord_count = 0
                        for social in enabled_social:
                            if isinstance(social, DiscordPlatform):
                                for status in platforms_went_offline:
                                    if social.end_stream(status.platform_name, status.stream_data or {}, status.url):
                                        discord_count += 1
                                        logger.debug(f"  ✓ Updated Discord embed for {status.platform_name}")
                        
                        # Post to non-Discord platforms asynchronously
                        non_discord_social = [s for s in enabled_social if not isinstance(s, DiscordPlatform)]
                        if non_discord_social:
                            post_results = post_to_social_async(
                                enabled_social=non_discord_social,
                                ai_generator=ai_generator,
                                is_stream_start=False,
                                platform_name=platform_names,
                                username=first_status.username,
                                title=first_status.title,
                                url='',
                                fallback_messages=platform_end_messages,
                                stream_data=None,
                                reply_to_ids=last_live_post_ids.copy()
                            )
                            
                            posted_count = discord_count + sum(1 for pid in post_results.values() if pid)
                        else:
                            posted_count = discord_count
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
                
                else:
                    # SEPARATE or THREAD MODE: Post for each platform
                    for idx, status in enumerate(platforms_went_offline):
                        platform_end_messages = end_messages.get(status.platform_name, [])
                        if not platform_end_messages:
                            logger.debug(f"  No end messages for {status.platform_name}")
                            continue
                        
                        logger.info(f"📢 Posting 'OFFLINE' announcement for {status.platform_name}/{status.username}")
                        
                        # Add delay between streaming platforms to prevent API burst
                        if idx > 0:
                            time.sleep(4)  # Wait 4 seconds between each streaming platform
                        
                        # Handle Discord separately (update embed)
                        discord_count = 0
                        for social in enabled_social:
                            if isinstance(social, DiscordPlatform):
                                if social.end_stream(status.platform_name, status.stream_data or {}, status.url):
                                    discord_count += 1
                                    logger.debug(f"  ✓ Updated Discord embed to show stream ended")
                        
                        # Determine reply_to_ids for threading
                        reply_to_ids = None
                        if end_threading_mode == 'thread':
                            # Thread to this platform's live announcement
                            reply_to_ids = status.last_post_ids.copy()
                        
                        # Post to non-Discord platforms asynchronously
                        non_discord_social = [s for s in enabled_social if not isinstance(s, DiscordPlatform)]
                        if non_discord_social:
                            post_results = post_to_social_async(
                                enabled_social=non_discord_social,
                                ai_generator=ai_generator,
                                is_stream_start=False,
                                platform_name=status.platform_name,
                                username=status.username,
                                title=status.title,
                                url='',
                                fallback_messages=platform_end_messages,
                                stream_data=None,
                                reply_to_ids=reply_to_ids
                            )
                            
                            posted_count = discord_count + sum(1 for pid in post_results.values() if pid)
                        else:
                            posted_count = discord_count
                        
                        if posted_count > 0:
                            logger.info(f"✓ Posted end message to {posted_count}/{len(enabled_social)} platform(s)")
            
            # Determine sleep time based on any active streams
            any_live = any(s.state == StreamState.LIVE for s in stream_statuses.values())
            if any_live:
                sleep_time = post_interval * 60  # POST_INTERVAL is now in minutes, not hours
                live_platforms = [s.platform_name for s in stream_statuses.values() if s.state == StreamState.LIVE]
                logger.info(f"⏰ Streams active ({', '.join(live_platforms)}), checking again in {post_interval} minute(s)")
            else:
                sleep_time = check_interval * 60
                logger.info(f"⏰ No streams live, checking again in {check_interval} minute(s)")
            
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Stream Daemon stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info(f"Retrying in {check_interval} minute(s)...")
            time.sleep(check_interval * 60)


if __name__ == "__main__":
    main()
