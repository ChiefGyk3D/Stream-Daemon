"""
Discord webhook platform implementation with per-platform webhook and role support.
"""

import logging
import os
import re
import time
from typing import Optional
from urllib.parse import urlparse
import requests
from stream_daemon.config import get_config, get_bool_config, get_secret

logger = logging.getLogger(__name__)


def _is_url_for_domain(url: str, domain: str) -> bool:
    """
    Safely check if a URL is for a specific domain.
    
    Args:
        url: The URL to check
        domain: The domain to match (e.g., 'kick.com', 'twitch.tv')
    
    Returns:
        True if the URL's hostname matches or is a subdomain of the domain
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        # Check exact match or subdomain (e.g., www.kick.com matches kick.com)
        return hostname == domain or hostname.endswith('.' + domain)
    except Exception:
        return False


class DiscordPlatform:
    """Discord webhook platform with flexible per-platform and per-username webhook and role support."""
    
    def __init__(self):
        self.name = "Discord"
        self.enabled = False
        self.webhook_url = None  # Default webhook
        self.webhook_urls = {}  # platform_name -> webhook_url mapping
        self.webhook_urls_per_user = {}  # "platform/username" -> webhook_url mapping
        self.role_id = None  # Default role
        self.role_mentions = {}  # platform_name -> role_id mapping
        self.role_mentions_per_user = {}  # "platform/username" -> role_id mapping
        self.active_messages = {}  # platform_name -> {message_id, webhook_url, last_update} tracking
        
    def authenticate(self):
        if not get_bool_config('Discord', 'enable_posting', default=False):
            return False
        
        # Get default webhook URL
        self.webhook_url = get_secret('Discord', 'webhook_url',
                                      secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                      secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                      doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
        
        # Get per-platform webhook URLs (optional - overrides default)
        for platform in ['twitch', 'youtube', 'kick']:
            platform_webhook = get_secret('Discord', f'webhook_{platform}',
                                         secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                         secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                         doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
            if platform_webhook:
                self.webhook_urls[platform] = platform_webhook
                logger.info(f"  • Discord webhook configured for {platform.upper()}")
        
        # Need at least one webhook (default or per-platform)
        if not self.webhook_url and not self.webhook_urls:
            return False
        
        # Get default role ID (optional)
        self.role_id = get_secret('Discord', 'role',
                                 secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                 secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                 doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
        
        # Get per-platform role IDs (optional - overrides default)
        for platform in ['twitch', 'youtube', 'kick']:
            platform_role = get_secret('Discord', f'role_{platform}',
                                      secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                      secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                      doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
            if platform_role:
                self.role_mentions[platform] = platform_role
                logger.info(f"  • Discord role configured for {platform.upper()}")
        
        # Get per-username webhook URLs and roles (optional - most specific, overrides everything)
        # Format: DISCORD_WEBHOOK_TWITCH_USERNAME or DISCORD_ROLE_YOUTUBE_USERNAME
        # This allows different Discord channels/roles for each streamer
        for platform in ['twitch', 'youtube', 'kick']:
            # We don't know usernames yet at authenticate() time, so we'll check dynamically
            # in the post() method. Just log that per-user config is supported.
            pass
        
        self.enabled = True
        if self.webhook_url:
            logger.info("✓ Discord webhook configured (default)")
        if self.webhook_urls:
            logger.info(f"✓ Discord webhooks configured ({len(self.webhook_urls)} platform-specific)")
        logger.info("  • Per-username webhooks/roles supported (DISCORD_WEBHOOK_PLATFORM_USERNAME)")
        return True
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None, username: Optional[str] = None) -> Optional[str]:
        if not self.enabled:
            return None
        
        # Determine which webhook to use for this platform/username combination
        # Priority: per-username > per-platform > default
        webhook_url = None
        lookup_key = None
        
        # Try per-username webhook first (most specific)
        if platform_name and username:
            lookup_key = f"{platform_name.lower()}_{username.lower()}"
            # Try to load per-user webhook dynamically if not cached
            if lookup_key not in self.webhook_urls_per_user:
                user_webhook = get_secret('Discord', f'webhook_{lookup_key}',
                                         secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                         secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                         doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
                if user_webhook:
                    self.webhook_urls_per_user[lookup_key] = user_webhook
                    logger.debug(f"  • Loaded Discord webhook for {platform_name}/{username}")
            
            webhook_url = self.webhook_urls_per_user.get(lookup_key)
        
        # Fall back to per-platform webhook
        if not webhook_url and platform_name and platform_name.lower() in self.webhook_urls:
            webhook_url = self.webhook_urls[platform_name.lower()]
        
        # Fall back to default webhook
        if not webhook_url:
            webhook_url = self.webhook_url
        
        if not webhook_url:
            logger.warning(f"⚠ No Discord webhook configured for {platform_name or 'default'}")
            return None
            
        try:
            # Extract URL from message for embed
            url_pattern = r'https?://[^\s]+'
            url_match = re.search(url_pattern, message)
            first_url = url_match.group() if url_match else None
            
            # Build Discord embed with rich card
            embed = None
            if first_url and stream_data:
                # Determine color and platform info from URL
                color = 0x9146FF  # Default purple
                platform_title = "Live Stream"
                
                if _is_url_for_domain(first_url, 'twitch.tv'):
                    color = 0x9146FF  # Twitch purple
                    platform_title = "🟣 Live on Twitch"
                elif _is_url_for_domain(first_url, 'youtube.com') or _is_url_for_domain(first_url, 'youtu.be'):
                    color = 0xFF0000  # YouTube red
                    platform_title = "🔴 Live on YouTube"
                elif _is_url_for_domain(first_url, 'kick.com'):
                    color = 0x53FC18  # Kick green
                    platform_title = "🟢 Live on Kick"
                
                # Get stream data
                stream_title = stream_data.get('title', 'Live Stream')
                viewer_count = stream_data.get('viewer_count')
                thumbnail_url = stream_data.get('thumbnail_url')
                game_name = stream_data.get('game_name')
                
                embed = {
                    "title": platform_title,
                    "description": stream_title if stream_title else "Stream is live!",
                    "url": first_url,
                    "color": color,
                }
                
                # Add fields for viewer count and game if available
                fields = []
                if viewer_count is not None:
                    fields.append({
                        "name": "👥 Viewers",
                        "value": f"{viewer_count:,}",
                        "inline": True
                    })
                if game_name:
                    fields.append({
                        "name": "🎮 Category",
                        "value": game_name,
                        "inline": True
                    })
                
                if fields:
                    embed["fields"] = fields
                
                # Add thumbnail if available
                if thumbnail_url:
                    embed["image"] = {"url": thumbnail_url}
                
                embed["footer"] = {"text": "Click to watch the stream!"}
            
            # Build content: LLM message + role mention
            content = message  # Start with the LLM-generated message
            
            # Add role mention if configured
            # Priority: per-username > per-platform > default
            role_to_mention = None
            
            # Try per-username role first (most specific)
            if lookup_key:
                # Try to load per-user role dynamically if not cached
                if lookup_key not in self.role_mentions_per_user:
                    user_role = get_secret('Discord', f'role_{lookup_key}',
                                          secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                                          secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                                          doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
                    if user_role:
                        self.role_mentions_per_user[lookup_key] = user_role
                        logger.debug(f"  • Loaded Discord role for {platform_name}/{username}")
                
                role_to_mention = self.role_mentions_per_user.get(lookup_key)
            
            # Fall back to per-platform role
            if not role_to_mention and platform_name and platform_name.lower() in self.role_mentions:
                role_to_mention = self.role_mentions[platform_name.lower()]
            
            # Fall back to default role
            if not role_to_mention:
                role_to_mention = self.role_id
            
            # Add role mention if we found one
            if role_to_mention:
                content += f" <@&{role_to_mention}>"
            
            # Build webhook payload
            data = {}
            if content:
                data["content"] = content
            if embed:
                data["embeds"] = [embed]
            
            # Add ?wait=true to get the message ID back
            webhook_url_with_wait = webhook_url + "?wait=true" if "?" not in webhook_url else webhook_url + "&wait=true"
            
            response = requests.post(webhook_url_with_wait, json=data, timeout=10)
            
            if response.status_code == 200:
                # Store message info for future updates
                message_data = response.json()
                message_id = message_data.get('id')
                if message_id and platform_name:
                    self.active_messages[platform_name.lower()] = {
                        'message_id': message_id,
                        'webhook_url': webhook_url,
                        'last_update': time.time(),
                        'original_content': content  # Store LLM message + role mention
                    }
                logger.info(f"✓ Discord embed posted (ID: {message_id})")
                return message_id
            else:
                logger.warning(f"⚠ Discord post failed with status {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"✗ Discord post failed: {e}")
            return None
    
    def update_stream(self, platform_name: str, stream_data: dict, stream_url: str) -> bool:
        """Update an existing Discord embed with fresh stream data (viewer count, thumbnail)."""
        if not self.enabled or not platform_name:
            return False
        
        platform_key = platform_name.lower()
        if platform_key not in self.active_messages:
            logger.debug(f"No active Discord message for {platform_name} to update")
            return False
        
        msg_info = self.active_messages[platform_key]
        message_id = msg_info['message_id']
        webhook_url = msg_info['webhook_url']
        
        try:
            # Determine color and platform info
            color = 0x9146FF  # Default purple
            platform_title = "Live Stream"
            
            if _is_url_for_domain(stream_url, 'twitch.tv') or platform_key == 'twitch':
                color = 0x9146FF
                platform_title = "🟣 Live on Twitch"
            elif _is_url_for_domain(stream_url, 'youtube.com') or _is_url_for_domain(stream_url, 'youtu.be') or platform_key == 'youtube':
                color = 0xFF0000
                platform_title = "🔴 Live on YouTube"
            elif _is_url_for_domain(stream_url, 'kick.com') or platform_key == 'kick':
                color = 0x53FC18
                platform_title = "🟢 Live on Kick"
            
            # Build updated embed
            stream_title = stream_data.get('title', 'Live Stream')
            viewer_count = stream_data.get('viewer_count')
            thumbnail_url = stream_data.get('thumbnail_url')
            game_name = stream_data.get('game_name')
            
            embed = {
                "title": platform_title,
                "description": stream_title,
                "url": stream_url,
                "color": color,
            }
            
            # Add fields for viewer count and game
            fields = []
            if viewer_count is not None:
                fields.append({
                    "name": "👥 Viewers",
                    "value": f"{viewer_count:,}",
                    "inline": True
                })
            if game_name:
                fields.append({
                    "name": "🎮 Category",
                    "value": game_name,
                    "inline": True
                })
            
            if fields:
                embed["fields"] = fields
            
            # Add thumbnail with cache-busting timestamp to force refresh
            if thumbnail_url:
                # Add timestamp to URL to force Discord to fetch new thumbnail
                separator = '&' if '?' in thumbnail_url else '?'
                embed["image"] = {"url": f"{thumbnail_url}{separator}_t={int(time.time())}"}
            
            # Add last updated timestamp in footer
            embed["footer"] = {"text": f"Last updated: {time.strftime('%H:%M:%S')} • Click to watch!"}
            
            # Keep original content (LLM message + role mention) from initial post
            content = msg_info.get('original_content', '')
            
            # Build update payload
            data = {}
            if content:
                data["content"] = content
            data["embeds"] = [embed]
            
            # PATCH the message via webhook
            edit_url = f"{webhook_url}/messages/{message_id}"
            response = requests.patch(edit_url, json=data, timeout=10)
            
            if response.status_code == 200:
                msg_info['last_update'] = time.time()
                logger.info(f"✓ Discord embed updated for {platform_name} (viewers: {viewer_count:,})" if viewer_count else f"✓ Discord embed updated for {platform_name}")
                return True
            else:
                logger.warning(f"⚠ Discord update failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Discord update failed: {e}")
            return False
    
    def clear_stream(self, platform_name: str) -> None:
        """Clear tracked message for a platform when stream ends."""
        platform_key = platform_name.lower()
        if platform_key in self.active_messages:
            del self.active_messages[platform_key]
            logger.debug(f"Cleared Discord message tracking for {platform_name}")
    
    def end_stream(self, platform_name: str, stream_data: dict, stream_url: str) -> bool:
        """Update Discord embed to show stream has ended, keeping VOD link and final stats."""
        if not self.enabled or not platform_name:
            return False
        
        platform_key = platform_name.lower()
        if platform_key not in self.active_messages:
            logger.debug(f"No active Discord message for {platform_name} to mark as ended")
            return False
        
        msg_info = self.active_messages[platform_key]
        message_id = msg_info['message_id']
        webhook_url = msg_info['webhook_url']
        
        try:
            # Get custom "stream ended" message from .env (configuration, NOT secrets)
            # These are user-facing messages, not sensitive data - they stay in .env
            ended_message = os.getenv(f'DISCORD_ENDED_MESSAGE_{platform_key.upper()}')
            
            if not ended_message:
                # Fall back to default ended message
                ended_message = os.getenv('DISCORD_ENDED_MESSAGE')
            
            if not ended_message:
                # Ultimate fallback if no config provided
                ended_message = "Thanks for joining! Tune in next time 💜"
            
            # Determine color and platform info (use muted colors for ended streams)
            color = 0x808080  # Gray for ended
            platform_title = "Stream Ended"
            
            if _is_url_for_domain(stream_url, 'twitch.tv') or platform_key == 'twitch':
                color = 0x6441A5  # Muted purple
                platform_title = "⏹️ Stream Ended - Twitch"
            elif _is_url_for_domain(stream_url, 'youtube.com') or _is_url_for_domain(stream_url, 'youtu.be') or platform_key == 'youtube':
                color = 0xCC0000  # Muted red
                platform_title = "⏹️ Stream Ended - YouTube"
            elif _is_url_for_domain(stream_url, 'kick.com') or platform_key == 'kick':
                color = 0x42C814  # Muted green
                platform_title = "⏹️ Stream Ended - Kick"
            
            # Build updated embed with ended message
            stream_title = stream_data.get('title', 'Stream')
            viewer_count = stream_data.get('viewer_count')
            thumbnail_url = stream_data.get('thumbnail_url')
            game_name = stream_data.get('game_name')
            
            embed = {
                "title": platform_title,
                "description": f"{ended_message}\n\n**{stream_title}**",
                "url": stream_url,  # Keep VOD link
                "color": color,
            }
            
            # Add fields for peak viewer count and game
            fields = []
            if viewer_count is not None:
                fields.append({
                    "name": "👥 Peak Viewers",
                    "value": f"{viewer_count:,}",
                    "inline": True
                })
            if game_name:
                fields.append({
                    "name": "🎮 Category",
                    "value": game_name,
                    "inline": True
                })
            
            if fields:
                embed["fields"] = fields
            
            # Keep final thumbnail
            if thumbnail_url:
                embed["image"] = {"url": thumbnail_url}
            
            # Add ended timestamp in footer
            embed["footer"] = {"text": f"Stream ended at {time.strftime('%H:%M:%S')} • Click for VOD"}
            
            # Keep role mention visible but don't ping again
            content = ""
            if platform_key in self.role_mentions:
                role_id = self.role_mentions[platform_key]
                content = f"<@&{role_id}>"
            elif self.role_id:
                content = f"<@&{self.role_id}>"
            
            # Build update payload
            data = {}
            if content:
                data["content"] = content
            data["embeds"] = [embed]
            
            # PATCH the message via webhook
            edit_url = f"{webhook_url}/messages/{message_id}"
            response = requests.patch(edit_url, json=data, timeout=10)
            
            if response.status_code == 200:
                # Clear tracking after successful update
                del self.active_messages[platform_key]
                logger.info(f"✓ Discord embed updated to show {platform_name} stream ended")
                return True
            else:
                logger.warning(f"⚠ Discord stream ended update failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Discord stream ended update failed: {e}")
            return False
