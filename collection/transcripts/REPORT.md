# Steven Schrembeck preservation archive — transcription report

Completed October 10, 2026 using ElevenLabs Scribe v2.

- **85/85 original recordings transcribed**, totaling **37.691 hours**: 63 audio recordings and 22 videos.
- **2 existing workplace transcripts reused** after two Cox videos were added during processing. All **87/87 current media files** have transcript associations.
- **0 transcription failures**. Exactly 85 paid endpoint submissions; no repeated submissions.
- Each new transcript has readable TXT/HTML, SRT, VTT, untouched API JSON, response metadata and a review JSON file. Word timestamps, neutral speaker labels, source hashes, dates, request parameters and available usage are retained.

[Open archive](../index.html) · [Search all transcripts offline](index.html) · [Review flagged passages](REVIEW.html) · [Source associations and job ledger](associations.json)

## Usage and budget

API responses report **$8.291636 USD before overages** and **45,604 credits** consumed. The authorized limit was $15; the conservative reserved amount was $11.520. This response-header valuation is not an invoice or a verified new cash charge. The Creator subscription's usage changed from 85 to 45,689 credits; current overage is recorded as {"amount": "0", "currency": "usd"}. The response-header credit total exactly matches the account usage increase (45,604 credits). No separate invoice charge has been verified. Overage extension remained disabled. See [usage-summary.json](usage-summary.json).

The published base rate checked for the run was [$0.22/hour](https://elevenlabs.io/pricing/api), or $8.29 estimated before tax for the original inventory. Small differences from this estimate reflect API metering. No paid keyterm, entity, editing, isolation or other add-ons were used. Local crosschecks incurred no ElevenLabs charges.

## Quality and review needs

Four full pilot recordings covered solo commentary, two-speaker conversation, an interview and fiction with music. Twelve beginning/middle/end extracts were independently crosschecked with local Whisper small.en before scaling. The independent model's output is evidence for comparison, not ground truth. 9 further beginning/middle/end checks cover the NoSleep recording, the long The Fix episode 2 video, and Reverie Teaser. All 21 crosschecks are preserved as evidence, with disagreements flagged.

The transcripts remain **uncorrected machine output**. No direct human listening review was performed in this session. Known issues include a misspelling of Steven's surname and a roughly 40-second opening-word alignment anomaly in Mortal Steel episode 1. Speaker labels can merge or split dramatic voices. Read the [pilot review](PILOT-REVIEW.md) and [review queue](review-queue.json) before using captions as authoritative quotations or publication-ready subtitles.

There are 57 recordings with automated review candidates: low_word_logprob: 101, catalog_name_spelling_review: 2, leading_no_speech: 14, trailing_no_speech: 18, word_duration_over_3s: 35, speech_gap_over_20s: 23, cross_recognizer_disagreement: 4, no_words: 3. Gaps may be intentional music or silence, and low-confidence words may be correct. Raw words and timings were retained; no silent corrections or invented identities were introduced. Corrected versions have not been created.

## Preservation and verification

All 457 original manifest entries passed the initial checksum verification. No exact original file duplicates or identical encoded audio-stream payloads were found; differently encoded or partial overlaps were not ruled out. Original media bytes remain unchanged. Full audio decoding found that some MP3 container durations were slightly underestimated; decoded durations, recorded separately, are used for subtitle bounds. The original 37.681-hour container estimate remains in the preflight evidence. Both existing workplace transcripts were reused without uploading those videos.

All 22 original video audio tracks were extracted to a separate working directory as FLAC without cutting, resampling or channel mixing. No recording required splitting. Source timestamp inspection established zero audio offset for all 22. Existing source metadata and retrieval history are preserved, with earlier metadata/checksum snapshots under provenance/.

Coverage, raw response hashes, subtitle cue numbering and time bounds, and active-page local links were checked. Byte-preserved historical HTML snapshots retain their original relative base and are excluded from active-page link validation. Verification reports 0 failures and 1415 checked local links. Overlapping captions caused by simultaneous speech are retained and counted. Unusually long word alignments are flagged rather than silently retimed. Offline search logic was tested locally; a rendered browser preview was unavailable because the browser tool blocks local-file URLs.

The three failed interview downloads already documented in the original collection remain acquisition gaps, not transcription failures. The concurrent Cox additions and their provenance are retained. Updated SHA256SUMS.txt covers the resulting archive, and earlier checksum manifests are preserved.

Nothing was published or submitted to the Internet Archive. Only the original 85 recordings were sent to ElevenLabs under the supplied authorization.
