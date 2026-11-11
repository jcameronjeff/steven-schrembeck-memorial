# Reality 101: A Journal of Impossible Experiences

The reading edition of Steven's *Reality 101* series: the trailer, the prologue, episodes 1 to 5, the three bonus audio journals, and selections from four earlier interviews. Compiled November 11, 2026.

The text is made from the archive's transcripts by cutting only. No word is added, replaced, or moved. `scripts/reality_book.py` enforces that for every paragraph, and the website build and the test suite both fail if a manuscript stops matching its transcript.

## Files

| Path | Contents | Edited by hand |
|---|---|---|
| `chapters/NN-slug.txt` | Chapter manuscripts. The only place the book's prose lives. | Yes |
| `book.json` | Title, parts and chapter order, each source's transcript, speakers and date, name-spelling corrections, per-chapter editorial notes. | Yes |
| `editorial/about.txt`, `sources.txt`, `sources-end.txt` | The editor's front and back matter. | Yes |
| `guide.json` | The reader's guide: quotations, practices, and the list of experiences. | Yes |
| `cover.svg` | Cover. | Yes |
| `reading.html` | Standalone web reading edition. | No, built |
| `reality-101-a-journal-of-impossible-experiences.epub` | EPUB 3. | No, built |
| `passage-map.json` | Every paragraph with its recording, speaker, times, original transcript wording and edited wording. | No, built |
| `validation.json` | Counts, retained words per chapter and speaker, name corrections applied, transcript hashes. | No, built |

## Commands

```sh
python3 scripts/reality_book.py worksheet ep1 --out /tmp/ep1.txt   # numbered transcript for an editor to read
python3 scripts/reality_book.py check                               # every chapter in book.json
python3 scripts/reality_book.py check content/reality-101/chapters/02-reality-101.txt --omitted 30
python3 scripts/reality_book.py build                               # rewrite the four built files
python3 -m unittest tests.test_reality_book
```

After changing any hand-edited file, run `build`, then `python3 scripts/build.py` to refresh the website page, and commit both. The tests fail if the built files are stale.

## Manuscript format

```
# Chapter Title
subtitle: Episode 1
source: ep1

## Section heading

@B0012 Steven
One paragraph of his words.

@B0013 Joshua
One paragraph of his words.

[note] One or two neutral sentences, printed as "Editor's context: ...".
```

| Line | Meaning |
|---|---|
| `# Title`, `subtitle:` | Chapter heading. Editorial. |
| `source: id` | The source in `book.json` that the following passages come from. |
| `## Heading` | Section heading. Editorial, not checked. |
| `[note] text` | Editor's context. Not checked against the transcript. |
| `@B0012 Name` | Start of a passage: the worksheet block where its first word is found, and the speaker. One paragraph follows. |
| `@B0012 Name any` | The transcript gave these words to the wrong speaker; match against all speakers. Counted in `validation.json`. |
| `@B0012 Name moved` | Deliberately out of recording order. Counted in `validation.json`. |
| `*text*` | Italics, for titles. |

## What the checker enforces

| Rule | Result if broken |
|---|---|
| Every word of a passage occurs, in order, in the named speaker's transcript from the cited block onward. | Error |
| No more than 150 source words are skipped between two retained words of one paragraph. | Error |
| The passage begins within 150 seconds of the cited block. | Error |
| Passages follow recording order and do not reuse words. | Error unless `moved` |
| A transcript misspelling listed in `spelling` is not printed. | Error |
| A paragraph cuts more than 30 words in one place, keeps under half of the stretch it spans, drops a negation, or runs past 240 words. | `review` line for a person to read |
| Every quotation in `guide.json` is found verbatim in the chapter it cites. | Build fails |

Comparison is by words only: case, punctuation, quotation marks, paragraph breaks and dashes are editorial. `spelling` in `book.json` maps a transcript spelling to the printed one (for example `stephen` to `steven`); each use is counted in `validation.json`.

## What this does not establish

- That the machine transcript heard each word correctly. No transcript has had a full listening review.
- That a cut preserved the speaker's emphasis. The `review` lines exist to make a person look at the riskiest cuts.
- That the selection is neutral. Part Three is a selection; what each chapter leaves out is described in the book's sources note and in `chapter_notes`.
- Speaker attribution in `11-the-technology-that-centers-you`: its transcript is the publisher's caption file, which has no speaker labels, so speakers there were assigned from context.

## Excluded

`interviews/beyond-logic-…` is the original publication of the prologue and is the same conversation. The CTO Show interview (2023) concerns AI product development. The NoSleep recording is fiction. None is represented.
