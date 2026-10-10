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

inventory.csv and inventory.json list downloaded sources and failures. manifest.jsonl preserves web/audio retrieval records; YouTube source details are in each .info.json. SHA256SUMS.txt covers retained files, including derivatives and metadata. audio-validation.json records successful media-container inspection of all 63 MP3s, including durations and codecs. This confirms readable containers, not a full human listening review. video-validation.json records successful container checks for all 24 saved videos (22 Seeking Minima videos and 2 Cox workplace recordings), including both video and audio streams.

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

## Cox workplace additions — October 10, 2026

**cox-workplace/** adds the two supplied workplace presentation transcripts and the Cox memorial export (29 posts, 2 comments, 2 embedded images). Start with cox-workplace/index.html. Original HTML, JSON and VTT files are preserved; readable transcripts and structured corpus records retain attribution and provenance. The presentations are Steven’s work; memorial posts are contributor recollections. See cox-workplace/README.md for source distinctions and verification limits. The two original downloaded workplace MP4 recordings have now been moved into their presentation folders and linked beside the transcripts. The archive now contains 63 audio recordings and 24 videos (87 media files). Recording dates from filenames and embedded metadata are September 24, 2025 and January 6, 2026; the latter differs from the memorial contributor’s 2025 attribution.


<!-- transcription-notes -->
## Machine transcription — October 10, 2026

The original 63 audio recordings and 22 Seeking Minima videos have Scribe v2 machine transcripts in **transcripts/machine/**. Start with **transcripts/index.html** for offline full-text search, readable transcripts, SRT/VTT subtitles and untouched API JSON. The two subsequently added Cox videos reuse their supplied transcripts; neither was sent for paid transcription. All 87 current media files have transcript associations in transcripts/associations.json.

Machine transcripts are uncorrected. New speaker labels are neutral and local to each recording. Words, names, speaker separation and timing can contain errors; review candidates and pilot findings are available in transcripts/REVIEW.html and transcripts/PILOT-REVIEW.md. Independent local recognition checks are not a human listening review. No corrected editions have been created. Supplied Cox captions retain their existing source attribution and provenance.

The 22 video audio tracks were extracted separately in this transcription chat's work/video-audio directory without cuts, resampling or channel mixing. No recording required splitting. All checked video audio offsets are zero relative to original playback; timing metadata is retained in transcripts/video-timing.json. Original media bytes are unchanged.

transcripts/provenance/ preserves metadata and checksums from before transcription and after the concurrent Cox additions. The original retrieval inventory and manifest remain intact; transcripts/transcription-manifest.jsonl adds transcription provenance, and SHA256SUMS.txt is refreshed to cover retained archive files. See transcripts/REPORT.md for coverage, costs and verification. Nothing has been published or submitted to the Internet Archive.
<!-- /transcription-notes -->
