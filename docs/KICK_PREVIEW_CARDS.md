# Kick Stream Preview Cards - Implementation Guide

## Overview

Kick.com uses CloudFlare security that blocks automated web scrapers from fetching Open Graph metadata. This prevents traditional link preview card generation on Bluesky and Mastodon.

**Solution**: Use Kick API stream metadata instead of scraping the page.

## Platforms

### ✅ Discord
**Status**: Fully Working  
**Method**: Rich embeds with Discord's native embed system  
**Features**:
- Stream title
- Live thumbnail (auto-refreshing)
- Viewer count
- Category/game
- Live updates

**Implementation**: Uses Discord webhook embeds with stream_data

### ✅ Bluesky  
**Status**: Now Working (Fixed!)  
**Method**: External embed with uploaded thumbnail  
**Features**:
- Stream title
- Viewer count and category in description
- Uploaded thumbnail image
- Clickable link

**Implementation**: 
- Detects `kick.com/` URLs with `stream_data` parameter
- Uses stream metadata instead of scraping
- Uploads thumbnail via `upload_blob()`
- Creates `AppBskyEmbedExternal` with metadata

**Before Fix**:
```python
if 'kick.com/' in first_url:
    # Kick.com blocks automated requests
    logger.info("Posting with clickable link only")
    embed = None
```

**After Fix**:
```python
if 'kick.com/' in first_url and stream_data:
    # Use provided stream metadata (CloudFlare bypass)
    title = stream_data.get('title')
    thumbnail_url = stream_data.get('thumbnail_url')
    # Upload thumbnail and create embed
    embed = models.AppBskyEmbedExternal.Main(...)
```

### ⚠️ Mastodon
**Status**: Working (Image Attachment Method)  
**Method**: Image attachment instead of preview card  
**Features**:
- Stream thumbnail as attached image
- Image alt text with viewer count and category
- Clickable Kick link in post text

**Why Different from Bluesky**:
- Mastodon servers scrape URLs server-side for preview cards
- Kick's CloudFlare blocks Mastodon servers from scraping
- Can't bypass CloudFlare on behalf of Mastodon server
- **Solution**: Upload thumbnail as image attachment instead

**Implementation**:
```python
# Download thumbnail
img_response = requests.get(thumbnail_url, headers=headers)

# Save to temp file
with tempfile.NamedTemporaryFile(delete=False, suffix='.webp') as tmp_file:
    tmp_file.write(img_response.content)
    tmp_path = tmp_file.name

# Upload to Mastodon with alt text
description = f"🔴 LIVE • {viewer_count:,} viewers • {game_name}"
media = mastodon.media_post(tmp_path, description=description)

# Attach to post
mastodon.status_post(message, media_ids=[media['id']])
```

**Result**: Users see the thumbnail image with the post, providing similar visual appeal to preview cards.

## Code Changes

### BlueskyPlatform.post() Enhancement

```python
def post(self, message: str, reply_to_id: Optional[str] = None, 
         platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
    # ... existing code ...
    
    # New: Use stream_data for Kick embeds
    if 'kick.com/' in first_url and stream_data:
        logger.info("Using stream metadata for Kick embed (CloudFlare bypass)")
        
        title = stream_data.get('title', 'Live on Kick')
        thumbnail_url = stream_data.get('thumbnail_url')
        
        # Upload thumbnail
        if thumbnail_url:
            img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
            if img_response.status_code == 200:
                upload_response = self.client.upload_blob(img_response.content)
                thumb_blob = upload_response.blob
        
        # Create embed
        viewer_count = stream_data.get('viewer_count', 0)
        game_name = stream_data.get('game_name', '')
        description = f"🔴 LIVE • {viewer_count:,} viewers • {game_name}"
        
        embed = models.AppBskyEmbedExternal.Main(
            external=models.AppBskyEmbedExternal.External(
                uri=first_url,
                title=title[:300],
                description=description[:1000],
                thumb=thumb_blob
            )
        )
```

### MastodonPlatform.post() Enhancement

```python
def post(self, message: str, reply_to_id: Optional[str] = None,
         platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
    # ... existing code ...
    
    # New: Attach thumbnail image if stream_data provided
    media_ids = []
    if stream_data:
        thumbnail_url = stream_data.get('thumbnail_url')
        if thumbnail_url:
            # Download thumbnail
            img_response = requests.get(thumbnail_url, headers=headers)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(img_response.content)
                tmp_path = tmp_file.name
            
            # Upload to Mastodon with alt text
            viewer_count = stream_data.get('viewer_count', 0)
            game_name = stream_data.get('game_name', '')
            description = f"🔴 LIVE • {viewer_count:,} viewers • {game_name}"
            
            media = self.client.media_post(tmp_path, description=description)
            media_ids.append(media['id'])
            
            # Clean up temp file
            os.unlink(tmp_path)
    
    # Post with attached media
    status = self.client.status_post(
        message,
        in_reply_to_id=reply_to_id,
        media_ids=media_ids if media_ids else None
    )
```

## Testing

### Test Bluesky Kick Embed

```bash
cd /home/chiefgyk3d/src/twitch-and-toot
doppler run -- python3 tests/test_bluesky_kick_embed.py
```

**Expected Output**:
```
✓ LIVE: [Stream Title]
  👥 13,796 viewers
  🎮 Just Chatting
  📸 Thumbnail: https://images.kick.com/...

✓ Posted to Bluesky (Post ID: at://...)

🎉 SUCCESS! Kick embed created with:
  • Title: [DROPS ON] BIG DAY HUGE DRAMA NEWS+...
  • Description: 🔴 LIVE • 13,796 viewers • Just Chatting
  • Thumbnail: Uploaded from https://images.kick.com/...
```

### Test Mastodon Kick Image

```bash
cd /home/chiefgyk3d/src/twitch-and-toot
doppler run -- python3 tests/test_mastodon_kick_image.py
```

**Expected Output**:
```
✓ LIVE: [Stream Title]
  👥 34,529 viewers
  🎮 Just Chatting
  📸 Thumbnail: https://images.kick.com/...

✓ Uploaded thumbnail to Mastodon (media ID: 115431763560519652)
✓ Posted to Mastodon (Post ID: 115431763663639761)

🎉 SUCCESS! Kick thumbnail attached with:
  • Title: [DROPS ON] BIG DAY HUGE DRAMA NEWS+...
  • Image Alt Text: 🔴 LIVE • 34,529 viewers • Just Chatting
  • Thumbnail: Downloaded from https://images.kick.com/...
```

### Verify in Bluesky

1. Open your Bluesky feed
2. Find the post
3. Should see:
   - Rich preview card
   - Stream thumbnail
   - Title, viewer count, category
   - Clickable link

### Verify in Mastodon

1. Open your Mastodon feed
2. Find the post
3. Should see:
   - Post text with Kick link
   - Stream thumbnail as attached image
   - Image description (hover/alt text) with viewer count and category
   - Clickable link in post text

## Stream Data Structure

The `stream_data` dict must contain:

```python
{
    'title': str,           # Stream title
    'viewer_count': int,    # Current viewer count
    'thumbnail_url': str,   # Thumbnail image URL
    'game_name': str        # Category/game name
}
```

This is automatically provided by:
- `KickPlatform.is_live()`
- `TwitchPlatform.is_live()`
- `YouTubePlatform.is_live()`

## Usage in Main Daemon

```python
# Check if stream is live
is_live, stream_data = kick.is_live(username)

if is_live and stream_data:
    # Post with stream_data for rich embeds/images
    message = f"🔴 {username} is live on Kick!\n{stream_data['title']}\nhttps://kick.com/{username}"
    
    # Bluesky gets rich embed card
    bluesky.post(message, platform_name='Kick', stream_data=stream_data)
    
    # Discord gets rich embed
    discord.post(message, platform_name='Kick', stream_data=stream_data)
    
    # Mastodon gets thumbnail as image attachment
    mastodon.post(message, platform_name='Kick', stream_data=stream_data)
```

## Benefits

1. **Bypasses CloudFlare**: Uses API data instead of web scraping
2. **More Reliable**: Direct from Kick API, always up-to-date
3. **Richer Data**: Includes viewer count and category
4. **Consistent**: Same data across Discord, Bluesky, and Mastodon
5. **No Dependencies**: Doesn't require web scraping libraries for Kick
6. **Works Everywhere**: Each platform gets appropriate format (embeds or images)

## Future Improvements

### Potential Enhancements
- [ ] Cache thumbnails to reduce API calls
- [ ] Support for thumbnail caching/CDN
- [ ] Add stream category emoji based on game
- [ ] Auto-cleanup of Mastodon temp files on error
- [ ] Support for multiple image formats (GIF, animated WebP)

### Platform Support Matrix

| Platform | Preview Card | Method | Status |
|----------|-------------|---------|---------|
| Discord | ✅ Full | Rich Embeds | Working |
| Bluesky | ✅ Full | External Embed + Upload | Working |
| Mastodon | ✅ Image | Media Attachment | Working |
| Matrix | 🔄 Pending | Not yet implemented | TBD |

## See Also

- `tests/test_bluesky_kick_embed.py` - Bluesky test script
- `tests/test_mastodon_kick_image.py` - Mastodon test script
- `stream-daemon.py` - BlueskyPlatform and MastodonPlatform implementations
- `KICK_API.md` - Kick API documentation
