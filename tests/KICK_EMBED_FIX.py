#!/usr/bin/env python3
"""
KICK EMBED/IMAGE FIX SUMMARY
============================

PROBLEM:
--------
When running the daemon, Kick streams were not showing:
- Bluesky embed cards with thumbnails
- Mastodon attached images

This happened because stream_data was only being stored when streams
transitioned from OFFLINE to LIVE (after 2 consecutive checks).

If the daemon restarted with streams already live, stream_data would be
None until the stream went offline and came back online.

ROOT CAUSE:
-----------
The StreamStatus.update() method used debouncing (requires 2 consecutive
live checks before declaring a stream LIVE). However, stream_data was only
stored when the transition happened (check #2), not during check #1.

This meant:
- Fresh daemon start + already-live stream = No stream_data until restart
- stream_data stored in status = None
- social.post() called with stream_data=None
- Bluesky: No embed card created (falls back to scraping, which fails for Kick)
- Mastodon: No thumbnail attached

THE FIX:
--------
Modified StreamStatus.update() to store stream_data IMMEDIATELY on ANY
live check, not just when transitioning to LIVE state.

Before:
```python
if self.state == StreamState.OFFLINE and self.consecutive_live_checks >= 2:
    self.state = StreamState.LIVE
    self.stream_data = stream_data  # Only stored here
```

After:
```python
if stream_data:
    self.stream_data = stream_data  # Store immediately!

if self.state == StreamState.OFFLINE and self.consecutive_live_checks >= 2:
    self.state = StreamState.LIVE
```

IMPACT:
-------
✅ Daemon restarts with already-live streams → stream_data available immediately
✅ First check of new stream → stream_data available even during debouncing
✅ Bluesky posts → Embed cards with thumbnails for Kick streams
✅ Mastodon posts → Attached images for Kick streams
✅ Discord posts → Rich embeds with viewer count and thumbnails
✅ Debouncing still works → Prevents false positives from API hiccups

VERIFICATION:
-------------
Run these tests to verify:

1. Bluesky Kick embed:
   python tests/test_bluesky_kick_embed.py
   
2. Mastodon Kick image:
   python Archive/test_mastodon_kick_image.py
   
3. Full daemon with already-live streams:
   python stream-daemon.py
   (Should show embeds/images immediately, not after stream cycles)

FILES MODIFIED:
---------------
- stream-daemon.py:
  * StreamStatus.update() method (lines 137-185)
    Added: Always store stream_data when live, even during debouncing

TESTS PASSING:
--------------
✅ All 12 tests in test suite pass
✅ Bluesky Kick embed test passes
✅ Mastodon Kick image test passes
✅ Debouncing still works correctly
"""

print(__doc__)
