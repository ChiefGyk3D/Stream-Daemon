"""
Bluesky social platform implementation with threading and rich embed support.
"""

import logging
import re
from typing import Optional
from atproto import Client, models, client_utils
from stream_daemon.config import get_config, get_bool_config, get_secret

logger = logging.getLogger(__name__)


class BlueskyPlatform:
    """Bluesky social platform with threading support."""
    
    def __init__(self):
        self.name = "Bluesky"
        self.enabled = False
        self.client = None
        
    def authenticate(self):
        if not get_bool_config('Bluesky', 'enable_posting', default=False):
            return False
            
        handle = get_config('Bluesky', 'handle')
        app_password = get_secret('Bluesky', 'app_password',
                                  secret_name_env='SECRETS_AWS_BLUESKY_SECRET_NAME',
                                  secret_path_env='SECRETS_VAULT_BLUESKY_SECRET_PATH',
                                  doppler_secret_env='SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
        
        if not all([handle, app_password]):
            return False
            
        try:
            self.client = Client()
            self.client.login(handle, app_password)
            self.enabled = True
            logger.info("✓ Bluesky authenticated")
            return True
        except Exception as e:
            logger.warning(f"✗ Bluesky authentication failed: {e}")
            return False
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
            
        try:
            # Use TextBuilder to create rich text with explicit links
            text_builder = client_utils.TextBuilder()
            
            # Parse message to find URLs and convert them to clickable links
            # Pattern matches http:// and https:// URLs
            url_pattern = r'https?://[^\s]+'
            last_pos = 0
            first_url = None  # Track first URL for embed card
            
            for match in re.finditer(url_pattern, message):
                # Add text before URL
                if match.start() > last_pos:
                    text_builder.text(message[last_pos:match.start()])
                
                # Add URL as clickable link
                url = match.group()
                text_builder.link(url, url)
                
                # Capture first URL for embed card
                if first_url is None:
                    first_url = url
                
                last_pos = match.end()
            
            # Add any remaining text after last URL
            if last_pos < len(message):
                text_builder.text(message[last_pos:])
            
            # Create embed card for the first URL if found
            embed = None
            if first_url:
                try:
                    # Special handling for Kick with stream_data - use provided metadata
                    if 'kick.com/' in first_url and stream_data:
                        logger.info(f"ℹ Using stream metadata for Kick embed (CloudFlare bypass)")
                        
                        title = stream_data.get('title', 'Live on Kick')
                        thumbnail_url = stream_data.get('thumbnail_url')
                        
                        # Upload thumbnail to Bluesky if available
                        thumb_blob = None
                        if thumbnail_url:
                            try:
                                import requests
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                }
                                img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                                if img_response.status_code == 200:
                                    upload_response = self.client.upload_blob(img_response.content)
                                    thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                            except Exception as img_error:
                                logger.warning(f"⚠ Could not upload Kick thumbnail: {img_error}")
                        
                        # Create external embed with stream metadata (no viewer count to avoid showing 0 at start)
                        game_name = stream_data.get('game_name', '')
                        description = f"🔴 LIVE"
                        if game_name:
                            description += f" • {game_name}"
                        
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else 'Live on Kick',
                                description=description[:1000],
                                thumb=thumb_blob if thumb_blob else None
                            )
                        )
                    elif 'kick.com/' in first_url:
                        # Kick.com without stream_data - blocks automated requests with CloudFlare security policies
                        # Links will still be clickable, just without embed cards
                        logger.info(f"ℹ Kick.com blocks automated requests, posting with clickable link only")
                        embed = None
                    elif stream_data and ('twitch.tv/' in first_url or 'youtube.com/' in first_url or 'youtu.be/' in first_url):
                        # Use stream_data for Twitch/YouTube if available (more reliable than scraping)
                        logger.info(f"ℹ Using stream metadata for embed")
                        
                        title = stream_data.get('title', 'Live Stream')
                        thumbnail_url = stream_data.get('thumbnail_url')
                        
                        # Upload thumbnail to Bluesky if available
                        thumb_blob = None
                        if thumbnail_url:
                            try:
                                import requests
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                }
                                img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                                if img_response.status_code == 200:
                                    upload_response = self.client.upload_blob(img_response.content)
                                    thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                            except Exception as img_error:
                                logger.warning(f"⚠ Could not upload thumbnail: {img_error}")
                        
                        # Create external embed with stream metadata (no viewer count to avoid showing 0 at start)
                        game_name = stream_data.get('game_name', '')
                        description = f"🔴 LIVE"
                        if game_name:
                            description += f" • {game_name}"
                        
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else 'Live Stream',
                                description=description[:1000],
                                thumb=thumb_blob if thumb_blob else None
                            )
                        )
                    else:
                        # For non-Kick URLs, scrape Open Graph metadata
                        import requests
                        from bs4 import BeautifulSoup
                        from urllib.parse import urlparse
                        
                        # Fetch the page with a realistic browser User-Agent
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                        }
                        
                        response = requests.get(first_url, headers=headers, timeout=10)
                        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Try Open Graph metadata first
                        og_title = soup.find('meta', property='og:title')
                        og_description = soup.find('meta', property='og:description')
                        og_image = soup.find('meta', property='og:image')
                        
                        # Fallback to Twitter Card metadata if OG tags not found
                        if not og_title:
                            og_title = soup.find('meta', attrs={'name': 'twitter:title'})
                        if not og_description:
                            og_description = soup.find('meta', attrs={'name': 'twitter:description'})
                        if not og_image:
                            og_image = soup.find('meta', attrs={'name': 'twitter:image'})
                        
                        title = og_title['content'] if og_title and og_title.get('content') else first_url
                        description = og_description['content'] if og_description and og_description.get('content') else ''
                        image_url = og_image['content'] if og_image and og_image.get('content') else None
                        
                        # Upload image to Bluesky if available
                        thumb_blob = None
                        if image_url:
                            try:
                                # Handle relative URLs
                                if image_url.startswith('//'):
                                    image_url = 'https:' + image_url
                                elif image_url.startswith('/'):
                                    parsed = urlparse(first_url)
                                    image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"
                                
                                img_response = requests.get(image_url, headers=headers, timeout=10)
                                if img_response.status_code == 200:
                                    # Upload image as blob and extract the blob reference
                                    upload_response = self.client.upload_blob(img_response.content)
                                    # The upload_blob returns a Response object with a blob attribute
                                    thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                            except Exception as img_error:
                                logger.warning(f"⚠ Could not upload thumbnail: {img_error}")
                        
                        # Create external embed with metadata
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else first_url,  # Limit title length
                                description=description[:1000] if description else '',  # Limit description length
                                thumb=thumb_blob if thumb_blob else None
                            )
                        )
                except Exception as embed_error:
                    logger.warning(f"⚠ Could not create embed card: {embed_error}")
                    embed = None
            
            if reply_to_id:
                # Threading on Bluesky requires parent and root references
                try:
                    # Get the parent post details
                    parent_response = self.client.app.bsky.feed.get_posts({'uris': [reply_to_id]})
                    
                    if not parent_response or not hasattr(parent_response, 'posts') or not parent_response.posts:
                        logger.warning(f"⚠ Could not fetch parent post, posting without thread")
                        response = self.client.send_post(text_builder, embed=embed)
                        return response.uri if hasattr(response, 'uri') else None
                    
                    parent_post = parent_response.posts[0]
                    
                    # Determine root: if parent has a reply, use its root, otherwise parent is root
                    if hasattr(parent_post.record, 'reply') and parent_post.record.reply:
                        root_ref = parent_post.record.reply.root
                    else:
                        # Parent is the root - create strong ref
                        root_ref = models.create_strong_ref(parent_post)
                    
                    # Create parent reference
                    parent_ref = models.create_strong_ref(parent_post)
                    
                    # Create reply reference
                    reply_ref = models.AppBskyFeedPost.ReplyRef(
                        parent=parent_ref,
                        root=root_ref
                    )
                    
                    # Send threaded post with rich text and embed
                    response = self.client.send_post(text_builder, reply_to=reply_ref, embed=embed)
                    return response.uri if hasattr(response, 'uri') else None
                    
                except Exception as thread_error:
                    logger.warning(f"⚠ Bluesky threading failed, posting without thread: {thread_error}")
                    # Fall back to non-threaded post
                    response = self.client.send_post(text_builder, embed=embed)
                    return response.uri if hasattr(response, 'uri') else None
            else:
                # Simple post without threading, with rich text and embed card
                response = self.client.send_post(text_builder, embed=embed)
                return response.uri if hasattr(response, 'uri') else None
                
        except Exception as e:
            logger.error(f"✗ Bluesky post failed: {e}")
            return None
