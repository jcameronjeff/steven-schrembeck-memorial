# Reality 101: A Journal of Impossible Experiences

The reading edition of Steven's *Reality 101* series: the trailer, the prologue, episodes 1 to 5, the three bonus audio journals, and selections from four earlier interviews, with a preface, chapter introductions, comparisons and essays by the editor, Jeff Cameron. Compiled November 11, 2026.

The book has two voices and the build keeps them apart. Chapters are the speakers' own words. Narration is the editor's.

The text is made from the archive's transcripts by cutting only. No word is added, replaced, or moved. `scripts/reality_book.py` enforces that for every paragraph, and the website build and the test suite both fail if a manuscript stops matching its transcript.

## Files

| Path | Contents | Edited by hand |
|---|---|---|
| `chapters/NN-slug.txt` | Chapter manuscripts. The only place the book's prose lives. | Yes |
| `book.json` | Title, parts and chapter order, each source's transcript, speakers and date, name-spelling corrections, per-chapter editorial notes. | Yes |
| `editorial/about.txt`, `sources.txt`, `sources-end.txt` | The editor's front and back matter. | Yes |
| `narration/*.txt` | The editor's voice: `preface`, `before-NN-slug` (introduction to a chapter), `after-NN-slug` (connections and questions), and the essays named in `book.json`. | Yes |
| `references.json` | Every source the narration may cite. Only cited entries are printed under Works cited. | Yes |
| `guide.json` | The reader's guide: quotations, practices, and the list of experiences. | Yes |
| `research/*.md` | The four research dossiers behind the editor's pages: the model of reality, contact and teachers, abilities and evidence, and contact after death. Each rates how close every parallel is, says whether Steven named the source, gives the skeptical reading, and marks what could not be verified. Not published on the site. | Reference |
| `listening-review.json` | About 200 places where the machine transcript looks wrong, with the recording time of each, whether the words were kept or cut, and what was probably said. A queue for a person with headphones. | Yes |
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

## Narration format

Plain paragraphs separated by blank lines. `## Heading`, `- ` lists and `1. ` lists work as usual.

| Marker | Meaning | Checked |
|---|---|---|
| `> [NN-slug] words` | A block quotation of a speaker from that chapter. | The words must occur verbatim in one passage of the chapter. |
| `{q:NN-slug\|words}` | An inline quotation, printed in quotation marks and linked to its passage. | Same. |
| `{cite:key}` or `{cite:key,key2}` | A citation, printed as the reference's short label and linked to Works cited. | The key must be in `references.json`. |
| `{ch:NN-slug}` | A link to a chapter by its title. | The chapter must exist. |

Quotations of other authors are not machine-checked. Paraphrase them, or quote only words seen at the cited URL.

A part in `book.json` may list `essays` (`{"file": "the-map", "title": "The Map"}`) as well as, or in place of, `chapters`.

## What the checker enforces

| Rule | Result if broken |
|---|---|
| Every word of a passage occurs, in order, in the named speaker's transcript from the cited block onward. | Error |
| No more than 150 source words are skipped between two retained words of one paragraph. | Error |
| The passage begins within 150 seconds of the cited block. | Error |
| Passages follow recording order and do not reuse words. | Error unless `moved` |
| A transcript misspelling listed in `spelling` is not printed. | Error |
| A paragraph cuts more than 30 words in one place, keeps under half of the stretch it spans, drops a negation, or runs past 240 words. | `review` line for a person to read |
| Every quotation of a speaker in `guide.json` and in `narration/` is found verbatim in the chapter it cites. | Build fails |
| Every `{cite:}` key is in `references.json` and every `{ch:}` names a chapter. | Build fails |

Comparison is by words only: case, punctuation, quotation marks, paragraph breaks and dashes are editorial. `spelling` in `book.json` maps a transcript spelling to the printed one (for example `stephen` to `steven`); each use is counted in `validation.json`.

## What this does not establish

- That the machine transcript heard each word correctly. No transcript has had a full listening review.
- That a cut preserved the speaker's emphasis. The `review` lines exist to make a person look at the riskiest cuts.
- That the editor's comparisons are right. The sources were confirmed to exist and to say what is attributed to them; how close a parallel is, and what it shows, is the editor's judgment.
- That the selection is neutral. Part Three is a selection; what each chapter leaves out is described in the book's sources note and in `chapter_notes`.
- Speaker attribution in `11-the-technology-that-centers-you`: its transcript is the publisher's caption file, which has no speaker labels, so speakers there were assigned from context.

## Excluded

`interviews/beyond-logic-…` is the original publication of the prologue and is the same conversation. The CTO Show interview (2023) concerns AI product development. The NoSleep recording is fiction. None is represented.
