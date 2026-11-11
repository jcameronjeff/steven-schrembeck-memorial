#!/usr/bin/env python3
"""Reality 101 reading edition: worksheets, fidelity check, and build.

The chapter manuscripts in content/reality-101/chapters/ are edited by cutting
only. Every word of every passage must appear, in order, in the cited
speaker's part of the cited transcript. This tool makes the worksheets editors
read, enforces that rule, and builds the book from the manuscripts.

  python3 scripts/reality_book.py worksheet SOURCE [--out FILE]
  python3 scripts/reality_book.py check [CHAPTER.txt ...] [--omitted N]
  python3 scripts/reality_book.py build

Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'content/reality-101'
COLLECTION = ROOT / 'collection'

MAX_GAP = 150        # most source words a single paragraph may skip between two kept words
WARN_GAP = 30        # internal cuts longer than this are reported for review
WARN_WORDS = 240     # paragraphs longer than this are reported
WARN_RATIO = 0.5     # kept / spanned below this is reported
START_DRIFT = 150.0  # seconds a passage may begin after its cited block starts
NEGATIONS = {'not', 'no', 'never', 'nothing', 'nobody', 'none', 'neither', 'nor', 'without', 'cannot'}

WORD = re.compile(r"[^\W_]+(?:'[^\W_]+)*")


def norm_tokens(text: str, spelling: dict[str, str] | None = None) -> list[str]:
    """Words only: case-insensitive, apostrophes unified, punctuation excluded."""
    text = text.replace('\u2019', "'").replace('\u2018', "'").lower()
    tokens = WORD.findall(text)
    if spelling:
        tokens = [spelling.get(token, token) for token in tokens]
    return tokens


def clock(seconds: float) -> str:
    seconds = max(0.0, seconds)
    whole = int(seconds)
    return f'{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}'


@dataclass
class Block:
    number: int
    start: float
    speaker: str | None
    text: str
    first: int = 0   # index of first token in Source.tokens
    last: int = -1

    @property
    def id(self) -> str:
        return f'B{self.number:04d}'


@dataclass
class Token:
    norm: str
    raw: str
    time: float
    speaker: str | None
    block: int


@dataclass
class Source:
    id: str
    meta: dict
    blocks: list[Block] = field(default_factory=list)
    tokens: list[Token] = field(default_factory=list)
    spelling: dict[str, str] = field(default_factory=dict)

    def block_by_id(self, block_id: str) -> Block | None:
        match = re.fullmatch(r'B(\d+)', block_id)
        if not match:
            return None
        number = int(match[1])
        return self.blocks[number - 1] if 1 <= number <= len(self.blocks) else None


def load_config() -> dict:
    return json.loads((BOOK / 'book.json').read_text(encoding='utf-8'))


def _phrases(pieces: list[tuple], phrases: dict[str, str]) -> list[tuple]:
    """Replace a mis-heard run of words with the term that was said, keeping the transcript's wording as `original`."""
    for heard, said in phrases.items():
        want = heard.split()
        out: list[tuple] = []
        index = 0
        while index < len(pieces):
            window = pieces[index:index + len(want)]
            if (len(window) == len(want) and all(not piece[3] for piece in window)
                    and [norm_tokens(piece[0]) for piece in window] == [[word] for word in want]):
                tail = re.search(r'[^\w\'\u2019]*$', window[-1][0])[0]
                out.append((said + tail, window[0][1], window[0][2], False, ' '.join(piece[0] for piece in window)))
                index += len(want)
            else:
                out.append(pieces[index])
                index += 1
        pieces = out
    return pieces


def _finish(source: Source, pieces: list[tuple], spelling: dict[str, str]) -> None:
    """Group (text, time, speaker, is_event[, original]) pieces into blocks and tokens."""
    names = source.meta.get('speakers', {})
    current: list[tuple] = []

    def flush() -> None:
        if not current:
            return
        speaker = names.get(current[0][2], current[0][2]) if current[0][2] is not None else None
        block = Block(len(source.blocks) + 1, current[0][1], speaker,
                      ' '.join(f'({p[0].strip("[]() ")})' if p[3] else p[0] for p in current))
        block.first = len(source.tokens)
        for text, time, _speaker, is_event, *original in current:
            if is_event:
                continue
            for raw in WORD.findall(text.replace('\u2019', "'").replace('\u2018', "'")):
                token = raw.lower()
                source.tokens.append(Token(spelling.get(token, token), original[0] if original else raw, time, speaker, block.number - 1))
        block.last = len(source.tokens) - 1
        source.blocks.append(block)
        current.clear()

    words = 0
    for piece in pieces:
        if current and piece[2] != current[0][2]:
            flush()
            words = 0
        current.append(piece)
        if not piece[3]:
            words += 1
        ends_sentence = piece[0].rstrip('"\u201d\')').endswith(('.', '?', '!'))
        if (words >= 90 and ends_sentence) or words >= 170:
            flush()
            words = 0
    flush()


def load_source(source_id: str, config: dict) -> Source:
    meta = config['sources'][source_id]
    # Transcript misspellings of names, corrected when matching and counted in the validation record.
    spelling = {**config.get('spelling', {}), **meta.get('spelling', {})}
    source = Source(source_id, meta, spelling=spelling)
    path = COLLECTION / meta['transcript']
    pieces: list[tuple[str, float, str | None, bool]] = []
    if meta.get('format', 'scribe') == 'scribe':
        data = json.loads(path.read_text(encoding='utf-8'))
        for word in data['words']:
            if word['type'] == 'spacing':
                continue
            pieces.append((word['text'], float(word.get('start') or 0.0), word.get('speaker_id'), word['type'] != 'word'))
    elif meta['format'] == 'srt':
        cue = re.compile(r'(\d+)\s*\n(\d\d):(\d\d):(\d\d)[,.](\d+)\s*-->[^\n]*\n(.*?)(?=\n\s*\n|\Z)', re.S)
        for match in cue.finditer(path.read_text(encoding='utf-8').replace('\r\n', '\n')):
            start = int(match[2]) * 3600 + int(match[3]) * 60 + int(match[4]) + int(match[5]) / 1000
            for word in match[6].split():
                pieces.append((word, start, None, False))
    else:
        raise ValueError(f'Unknown transcript format for {source_id}')
    _finish(source, _phrases(pieces, meta.get('phrases', {})), spelling)
    return source


def worksheet(source: Source) -> str:
    names = sorted({block.speaker for block in source.blocks if block.speaker})
    lines = [f'SOURCE {source.id} — {source.meta["title"]}',
             'Speakers: ' + (', '.join(names) if names else 'not labelled in this transcript (identify from context)'),
             'Machine transcript, uncorrected. (parentheses) mark sounds, not words.', '']
    for block in source.blocks:
        who = f' {block.speaker}' if block.speaker else ''
        lines.append(f'[{block.id} {clock(block.start)}{who}] {block.text}')
        lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------- manuscripts

@dataclass
class Passage:
    line: int
    block_id: str
    speaker: str
    flags: set[str]
    text: str
    source: str = ''
    id: str = ''
    kept: list[int] = field(default_factory=list)   # indexes into Source.tokens


@dataclass
class Chapter:
    path: Path
    slug: str
    title: str = ''
    subtitle: str = ''
    items: list[tuple[str, object]] = field(default_factory=list)  # ('h2'|'note'|'passage', value)

    @property
    def passages(self) -> list[Passage]:
        return [value for kind, value in self.items if kind == 'passage']


HEADER = re.compile(r'@(B\d+)\s+([^\s]+)((?:\s+(?:moved|any|verse))*)\s*$')


def parse_chapter(path: Path) -> tuple[Chapter, list[str]]:
    chapter = Chapter(path, path.stem)
    errors: list[str] = []
    source = ''
    lines = path.read_text(encoding='utf-8').split('\n')
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        number = index + 1
        if not line.strip():
            index += 1
        elif line.startswith('# '):
            chapter.title = line[2:].strip()
            index += 1
        elif line.startswith('## '):
            chapter.items.append(('h2', line[3:].strip()))
            index += 1
        elif line.startswith('subtitle:'):
            chapter.subtitle = line.split(':', 1)[1].strip()
            index += 1
        elif line.startswith('source:'):
            source = line.split(':', 1)[1].strip()
            index += 1
        elif line.startswith('[note]'):
            text = [line[6:].strip()]
            index += 1
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(('@', '#', '[note]', 'source:')):
                text.append(lines[index].strip())
                index += 1
            chapter.items.append(('note', ' '.join(text)))
        elif line.startswith('@'):
            match = HEADER.match(line)
            if not match:
                errors.append(f'{path.name}:{number}: unreadable passage header "{line}" (expected "@B0123 Name")')
                index += 1
                continue
            text = []
            index += 1
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(('@', '## ', '# ', '[note]', 'source:')):
                text.append(lines[index].strip())
                index += 1
            flags = set(match[3].split())
            passage = Passage(number, match[1], match[2], flags, ('\n' if 'verse' in flags else ' ').join(text), source)
            if not passage.text:
                errors.append(f'{path.name}:{number}: passage {match[1]} has no text')
            if not source:
                errors.append(f'{path.name}:{number}: passage appears before any "source:" line')
            chapter.items.append(('passage', passage))
        else:
            errors.append(f'{path.name}:{number}: text outside a passage: "{line[:60]}"')
            index += 1
    if not chapter.title:
        errors.append(f'{path.name}: missing "# Title" line')
    for count, passage in enumerate(chapter.passages, 1):
        passage.id = f'c{chapter.slug[:2]}-p{count:03d}'
    return chapter, errors


def _context(source: Source, index: int, count: int = 28) -> str:
    speaker = source.tokens[index].speaker if 0 <= index < len(source.tokens) else None
    words = [token.raw for token in source.tokens[max(index, 0):index + count * 2] if token.speaker == speaker][:count]
    return ' '.join(words)


def check_chapter(chapter: Chapter, sources: dict[str, Source]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    cursor: dict[tuple[str, str | None], int] = {}
    previous_start: dict[str, int] = {}
    for passage in chapter.passages:
        where = f'{chapter.path.name}:{passage.line} {passage.block_id}'
        source = sources.get(passage.source)
        if source is None:
            errors.append(f'{where}: unknown source "{passage.source}"')
            continue
        block = source.block_by_id(passage.block_id)
        if block is None:
            errors.append(f'{where}: no such block in {source.id}')
            continue
        labelled = any(item.speaker for item in source.blocks)
        any_speaker = 'any' in passage.flags or not labelled
        if labelled:
            known = {item.speaker for item in source.blocks}
            if passage.speaker not in known:
                errors.append(f'{where}: speaker "{passage.speaker}" is not in this source ({", ".join(sorted(known))})')
                continue
            if not any_speaker and block.speaker != passage.speaker:
                errors.append(f'{where}: block is spoken by {block.speaker}, not {passage.speaker}')
                continue
        if re.search(r'[\[\]]|Speaker \d', passage.text):
            errors.append(f'{where}: remove bracketed tags or speaker labels from the text')
        misspelt = sorted({token for token in norm_tokens(passage.text) if token in source.spelling})
        if misspelt:
            errors.append(f'{where}: write ' + ', '.join(f'"{source.spelling[token]}" for "{token}"' for token in misspelt))
        edited = norm_tokens(passage.text, source.spelling)
        if not edited:
            continue
        eligible = [i for i in range(len(source.tokens))
                    if any_speaker or source.tokens[i].speaker == passage.speaker]
        key = (source.id, None if any_speaker else passage.speaker)
        begin = block.first
        if 'moved' not in passage.flags:
            if block.last < cursor.get(key, 0):
                errors.append(f'{where}: this block comes before words an earlier passage already used. '
                              f'Keep recording order, or add "moved" to the header if the reordering is deliberate.')
                continue
            begin = max(begin, cursor.get(key, 0))
        position = next((p for p, i in enumerate(eligible) if i >= begin), len(eligible))
        forward: list[int] = []
        failed = False
        for count, token in enumerate(edited):
            while position < len(eligible) and source.tokens[eligible[position]].norm != token:
                position += 1
            if position == len(eligible):
                last = eligible[forward[-1]] if forward else begin
                before = ' '.join(edited[max(0, count - 6):count])
                errors.append(f'{where}: "{token}" is not in the source after "… {before}". '
                              f'Source continues at {source.blocks[source.tokens[min(last, len(source.tokens) - 1)].block].id}: '
                              f'"{_context(source, last)}"')
                failed = True
                break
            forward.append(position)
            position += 1
        if failed:
            continue
        # Tighten from the end so the alignment hugs the words actually used.
        position = forward[-1]
        tight: list[int] = []
        for token in reversed(edited):
            while source.tokens[eligible[position]].norm != token:
                position -= 1
            tight.append(position)
            position -= 1
        tight.reverse()
        gap_error = False
        for count in range(1, len(tight)):
            skipped = tight[count] - tight[count - 1] - 1
            if skipped > MAX_GAP:
                at = eligible[tight[count - 1]]
                errors.append(f'{where}: between "{edited[count - 1]}" and "{edited[count]}" the paragraph skips '
                              f'{skipped} source words. Either "{edited[count]}" is not what was said here, or this '
                              f'should be two passages. Source after "{edited[count - 1]}" at '
                              f'{source.blocks[source.tokens[at].block].id}: "{_context(source, at)}"')
                gap_error = True
                break
        if gap_error:
            continue
        passage.kept = [eligible[p] for p in tight]
        first, last = passage.kept[0], passage.kept[-1]
        drift = source.tokens[first].time - block.start
        if drift > START_DRIFT:
            errors.append(f'{where}: the text begins {int(drift)} s after the cited block, at '
                          f'{source.blocks[source.tokens[first].block].id}. Cite the block where the passage starts.')
            continue
        if 'moved' not in passage.flags and first < previous_start.get(source.id, -1):
            errors.append(f'{where}: this passage comes before the previous one in the recording. '
                          f'Keep recording order, or add "moved" to the header if the reordering is deliberate.')
        previous_start[source.id] = first
        cursor[key] = max(cursor.get(key, 0), last + 1)
        spanned = tight[-1] - tight[0] + 1
        kept = set(tight)
        dropped = [source.tokens[eligible[p]] for p in range(tight[0], tight[-1] + 1) if p not in kept]
        if spanned and len(edited) / spanned < WARN_RATIO and spanned > 60:
            warnings.append(f'{where}: keeps {len(edited)} of {spanned} words; check that the cuts leave his meaning intact')
        for count in range(1, len(tight)):
            skipped = tight[count] - tight[count - 1] - 1
            if skipped > WARN_GAP:
                cut = ' '.join(source.tokens[eligible[p]].raw for p in range(tight[count - 1] + 1, min(tight[count], tight[count - 1] + 15)))
                warnings.append(f'{where}: cuts {skipped} words mid-paragraph after "{edited[count - 1]}": "{cut} …"')
        retained_norms = set(edited)
        lost = sorted({t.norm for t in dropped if (t.norm in NEGATIONS or t.norm.endswith("n't")) and t.norm not in retained_norms})
        if lost:
            warnings.append(f'{where}: drops {", ".join(lost)}; confirm only a false start or repetition was cut')
        if len(edited) > WARN_WORDS:
            warnings.append(f'{where}: {len(edited)} words; consider a paragraph break')
    return errors, warnings


def coverage(chapters: list[Chapter], sources: dict[str, Source], omitted: int = 0) -> list[str]:
    lines: list[str] = []
    used: dict[str, set[int]] = {}
    for chapter in chapters:
        for passage in chapter.passages:
            used.setdefault(passage.source, set()).update(passage.kept)
    for source_id, kept in used.items():
        source = sources[source_id]
        speakers = sorted({token.speaker for token in source.tokens}, key=lambda s: s or '')
        for speaker in speakers:
            total = sum(token.speaker == speaker for token in source.tokens)
            mine = sum(source.tokens[i].speaker == speaker for i in kept)
            lines.append(f'{source_id}: {speaker or "all speakers"} — kept {mine} of {total} words ({mine / total:.0%})' if total else '')
        if omitted:
            runs: list[tuple[int, int, int]] = []
            for speaker in speakers:
                indexes = [i for i, token in enumerate(source.tokens) if token.speaker == speaker]
                start = None
                for position, i in enumerate(indexes + [-1]):
                    if i != -1 and i not in kept:
                        start = position if start is None else start
                    elif start is not None:
                        runs.append((position - start, indexes[start], indexes[position - 1]))
                        start = None
            runs.sort(reverse=True)
            for size, first, last in runs[:omitted]:
                token = source.tokens[first]
                lines.append(f'  omitted {size:4d} words  {source.blocks[token.block].id}–{source.blocks[source.tokens[last].block].id} '
                             f'{clock(token.time)} {token.speaker or ""}: {_context(source, first, 14)} …')
    return [line for line in lines if line]


def load_chapters(paths: list[Path] | None, config: dict) -> tuple[list[Chapter], list[str]]:
    if not paths:
        paths = [BOOK / 'chapters' / f'{slug}.txt' for part in config['parts'] for slug in part['chapters']]
    chapters: list[Chapter] = []
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f'{path}: missing chapter manuscript')
            continue
        chapter, problems = parse_chapter(path)
        chapters.append(chapter)
        errors.extend(problems)
    return chapters, errors


def run_check(paths: list[Path] | None, omitted: int = 0, quiet: bool = False):
    config = load_config()
    chapters, errors = load_chapters(paths, config)
    sources: dict[str, Source] = {}
    warnings: list[str] = []
    for chapter in chapters:
        for passage in chapter.passages:
            if passage.source in config['sources'] and passage.source not in sources:
                sources[passage.source] = load_source(passage.source, config)
        found, noted = check_chapter(chapter, sources)
        errors.extend(found)
        warnings.extend(noted)
    if not quiet:
        for line in warnings:
            print('review ', line)
        for line in errors:
            print('ERROR  ', line)
        for line in coverage(chapters, sources, omitted):
            print(line)
        words = sum(len(norm_tokens(p.text)) for c in chapters for p in c.passages)
        print(f'{len(chapters)} chapter(s), {sum(len(c.passages) for c in chapters)} passages, {words} words, '
              f'{len(errors)} error(s), {len(warnings)} to review')
    return chapters, sources, errors, warnings, config


# ---------------------------------------------------------------------- build

def smart(text: str) -> str:
    """Typographic quotes and dashes; wording is untouched."""
    text = re.sub(r'\s*--\s*', ' \u2014 ', text)
    text = text.replace('...', '\u2026')
    text = re.sub(r"(^|[\s(\[\u2014\"\u201c])'(?=(?:cause|em|til|bout|round|\d0s)\b)", '\\1\u2019', text)
    text = re.sub(r'(^|[\s(\[\u2014])"', '\\1\u201c', text)
    text = text.replace('"', '\u201d')
    text = re.sub(r"(^|[\s(\[\u2014\u201c])'", '\\1\u2018', text)
    return text.replace("'", '\u2019')


def inline(text: str) -> str:
    text = html.escape(smart(text), quote=False)
    return re.sub(r'\*([^*\n]+)\*', r'<em>\1</em>', text)


def chapter_html(chapter: Chapter, number: str, level: int, labels: bool) -> str:
    out = [f'<h{level} id="chapter-{number}">{inline(chapter.title)}</h{level}>']
    if chapter.subtitle:
        out.append(f'<p class="chapter-subtitle">{inline(chapter.subtitle)}</p>')
    speaker = None
    for kind, value in chapter.items:
        if kind == 'h2':
            anchor = f'chapter-{number}-' + re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
            out.append(f'<h{level + 1} id="{anchor}">{inline(value)}</h{level + 1}>')
            speaker = None
        elif kind == 'note':
            out.append(f'<p class="editor-note"><strong>Editor\u2019s context:</strong> {inline(value)}</p>')
            speaker = None
        else:
            label = ''
            if labels and value.speaker != speaker:
                label = f'<span class="speaker">{html.escape(value.speaker)}</span> '
            speaker = value.speaker
            cls = 'passage' + ('' if not labels else ' voice-' + re.sub(r'[^a-z]', '', value.speaker.lower()))
            out.append(f'<div id="{value.id}" class="{cls}"><p>{label}{inline(value.text)}</p></div>')
    return '\n'.join(out)


def passage_record(passage: Passage, chapter: Chapter, sources: dict[str, Source]) -> dict:
    source = sources[passage.source]
    first, last = passage.kept[0], passage.kept[-1]
    labelled = any(block.speaker for block in source.blocks)
    span = [t for t in source.tokens[first:last + 1]
            if 'any' in passage.flags or not labelled or t.speaker == passage.speaker]
    return {'id': passage.id, 'chapter': chapter.slug, 'source': passage.source,
            'source_title': source.meta['title'], 'transcript': source.meta['transcript'],
            'speaker': passage.speaker, 'start': clock(source.tokens[first].time),
            'end': clock(source.tokens[last].time), 'original': ' '.join(t.raw for t in span),
            'edited': passage.text, 'source_window_words': len(span), 'retained_words': len(passage.kept),
            **({'moved': True} if 'moved' in passage.flags else {})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sheet = sub.add_parser('worksheet')
    sheet.add_argument('source')
    sheet.add_argument('--out', type=Path)
    check = sub.add_parser('check')
    check.add_argument('chapters', nargs='*', type=Path)
    check.add_argument('--omitted', type=int, default=0, help='list the N longest uncut stretches left out')
    sub.add_parser('build')
    args = parser.parse_args()
    if args.command == 'worksheet':
        text = worksheet(load_source(args.source, load_config()))
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding='utf-8')
            print(f'{args.out}: {len(text.split())} words')
        else:
            sys.stdout.write(text)
    elif args.command == 'check':
        errors = run_check([p.resolve() for p in args.chapters] or None, args.omitted)[2]
        raise SystemExit(1 if errors else 0)
    else:
        from reality_book_build import build
        build()


if __name__ == '__main__':
    main()
