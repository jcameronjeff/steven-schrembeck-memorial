# Steven Schrembeck — local preservation archive

Collected October 10, 2026, starting from https://remembering-steven-schrembeck.opzero.sh/.

Open **index.html** to browse the collection and play saved audio. Nothing has been uploaded to the Internet Archive.

## Contents

- **memorial/**: original memorial HTML, two photographs, and an offline reading copy. The offline copy uses local photographs and omits the tracking image.
- **blog/**: 19 article pages plus the home page of A Different Compass, original HTML, embedded page data, plain text, available images, and a combined offline reading copy (READ.html). Original HTML may still request online assets; use the reading copy for offline text. This covers linked articles plus six older published entries found in the publicly served page data, not a guarantee that every historical post was discovered. Two visibly linked pages (Cheat and Reality 102: Souls) have an internal Unpublished status despite being publicly linked; review that discrepancy before publication. Entries marked Unpublished that were not visibly linked were not separately fetched.
- **reality/**: all 10 audio enclosures exposed by the current Reality 101 feed, including trailers and updates, with the feed, cover, and episode metadata.
- **collected/**: all 47 audio enclosures exposed by the current Collected feed, with the feed, cover, and episode metadata.
- **interviews/**: six additional recordings recovered from the appearances listed at https://talks.co/reality101/. Includes Alien Spirit, Unlocking human and machine consciousness, Beyond Logic, The CTO Show #107, #1300 Empowering Minds with AI, and NoSleep Podcast S9E09. These are whole guest-show recordings; appearance attribution and exact correspondence to the originally linked interview should be checked before submission.
- **youtube/**: Seeking Minima videos, descriptions, thumbnails, and source metadata. The channel lists 11 regular videos and 11 Shorts (22 total); its streams tab is unavailable. Download selection is available video up to 1080p landscape or 1080×1920 portrait and 30 fps with separate audio merged without re-encoding; these are platform delivery copies, not upload masters. All 22 listed videos are saved. The inventory and download logs identify completed videos.
- **discovery/**: source catalogs and feed lookups retained as research evidence.

## Provenance and verification

inventory.csv and inventory.json list downloaded sources and failures. manifest.jsonl preserves web/audio retrieval records; YouTube source details are in each .info.json. SHA256SUMS.txt covers retained files, including derivatives and metadata. audio-validation.json records successful media-container inspection of all 63 MP3s, including durations and codecs. This confirms readable containers, not a full human listening review. video-validation.json records successful container checks for all 22 completed videos, including both video and audio streams.

The raw HTML, feeds, and media are retained separately from generated reading copies and the index. Response headers record HTTP retrieval details. Files ending in .part or .ytdl are incomplete and must not be submitted.

## Known gaps and follow-up

1. The blog RSS returned an empty feed; articles were collected directly from the website instead.
2. Five blog image requests failed with HTTP 419 (expired source links). Article text and embedded page data were retained.
3. Three guest appearances were not downloaded: **Fastest way to Get Great And Take Your Goals All The Way** (403), **An Unwelcome Audience** (403), and **The Technology That Centers You | 79** (404). Source URLs and errors are in the inventory.
4. The Apple link on the memorial currently resolves to a broad KGRA feed that does not expose the named interview. An Alien Spirit recording naming Steven was recovered through his appearances profile; whether this is the exact same recording as the original Apple episode remains unverified.
5. Both the regular videos and Shorts tabs were inventoried; no streams tab was available. Unavailable/deleted uploads, social posts, repositories, older websites, and unlinked works have not been exhaustively searched.
6. Review titles, dates, attribution, and publication permission with the relevant rights holders before an Internet Archive submission. No license or permission is inferred from public accessibility.

The original collection site remains the starting catalog. This archive is a first preservation pass, with explicit gaps, rather than a claim to be Steven's complete lifetime works.


Initial loading-shell responses for five older blog routes are retained in discovery/initial-page-responses; a later request returned the full articles. The inventory uses the latest successful capture for each path, while manifest.jsonl retains retrieval history. Incomplete files from early interrupted video attempts were moved outside this deliverable.
