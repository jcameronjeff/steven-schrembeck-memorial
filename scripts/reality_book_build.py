"""Build the Reality 101 reading edition from its checked manuscripts.

Outputs, all in content/reality-101/: reading.html, the EPUB, passage-map.json
and validation.json. The website builder imports render_site() for its page.

Two voices are kept apart. Chapter passages are the speakers' own words and are
checked against the transcripts by reality_book.py. The editor's narration
(content/reality-101/narration/) is new writing; when it quotes Steven the
quotation must be found verbatim in the chapter it names, and every source it
cites must be in references.json, or the build fails.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

from reality_book import (BOOK, COLLECTION, Chapter, Source, clock, inline, norm_tokens,
                          passage_record, run_check)

ARCHIVE = 'https://steven-schrembeck-archive.opzero.sh/'
EPUB_NAME = 'reality-101-a-journal-of-impossible-experiences.epub'
ORDINALS = ['One', 'Two', 'Three', 'Four', 'Five', 'Six']
STAMP = (2026, 11, 11, 0, 0, 0)
CITE = re.compile(r'\{cite:([^}|]+)(?:\|([^}]+))?\}')
CHAPTER_LINK = re.compile(r'\{ch:([^}]+)\}')
STEVEN_QUOTE = re.compile(r'>\s*\[([^\]]+)\]\s*(.+)', re.S)
INLINE_QUOTE = re.compile(r'\{q:([^|}]+)\|([^}]+)\}')
MARKER = re.compile(r'(\{(?:q|cite|ch):[^}]+\})')

Href = Callable[[str], str]


@dataclass
class Section:
    id: str            # anchor of its heading
    kind: str          # front | part | chapter | essay | back
    title: str
    file: str          # EPUB file name
    render: Callable[[int, Href, Callable[[str], str]], str]
    anchors: list[str]


def blocks_of(text: str) -> list[str]:
    return [block.strip() for block in re.split(r'\n\s*\n', text.strip()) if block.strip()]


def prose(text: str, level: int) -> str:
    """Editorial text: blank-line paragraphs, '## ' subheads, '- ' lists, *emphasis*."""
    out: list[str] = []
    for block in blocks_of(text):
        if block.startswith('## '):
            out.append(f'<h{level}>{inline(block[3:])}</h{level}>')
        elif block.startswith('- '):
            items = ''.join(f'<li>{inline(line[2:].strip())}</li>' for line in block.split('\n'))
            out.append(f'<ul>{items}</ul>')
        else:
            out.append(f'<p>{inline(" ".join(line.strip() for line in block.split(chr(10))))}</p>')
    return '\n'.join(out)


def chapter_passages(chapter: Chapter, level: int) -> str:
    speakers = {passage.speaker for passage in chapter.passages}
    labels = len(speakers) > 1
    out: list[str] = []
    speaker = None
    for kind, value in chapter.items:
        if kind == 'h2':
            out.append(f'<h{level + 1}>{inline(value)}</h{level + 1}>')
            speaker = None
        elif kind == 'note':
            out.append(f'<p class="editor-note"><strong>Editor’s context:</strong> {inline(value)}</p>')
            speaker = None
        else:
            label = ''
            if labels and value.speaker != speaker:
                label = f'<span class="speaker">{html.escape(value.speaker)}:</span> '
            speaker = value.speaker
            voice = ' voice-steven' if value.speaker == 'Steven' else ' voice-other'
            if 'verse' in value.flags:
                body = '<br />'.join(inline(line) for line in value.text.split('\n'))
                out.append(f'<div id="{value.id}" class="passage verse"><p>{body}</p></div>')
            else:
                out.append(f'<div id="{value.id}" class="passage{voice if labels else ""}"><p>{label}{inline(value.text)}</p></div>')
    return '\n'.join(out)


class Edition:
    def __init__(self) -> None:
        chapters, sources, errors, warnings, config = run_check(None, quiet=True)
        if errors:
            raise SystemExit('The manuscripts do not match their sources:\n' + '\n'.join(errors))
        self.config = config
        self.sources: dict[str, Source] = sources
        self.warnings = warnings
        self.chapters = {chapter.slug: chapter for chapter in chapters}
        self.guide = json.loads((BOOK / 'guide.json').read_text(encoding='utf-8'))
        self.editorial = {path.stem: path.read_text(encoding='utf-8') for path in sorted((BOOK / 'editorial').glob('*.txt'))}
        self.references = {ref['key']: ref for ref in json.loads((BOOK / 'references.json').read_text(encoding='utf-8'))}
        self.problems: list[str] = []
        self.cited: list[str] = []
        self.quote_targets: dict[tuple[str, str], str] = {}
        self.quoted = 0
        self.narration_words = 0
        self.narration = {path.stem: self._parse_narration(path.stem, path.read_text(encoding='utf-8'))
                          for path in sorted((BOOK / 'narration').glob('*.txt'))}
        self.sections = self._sections()
        if self.problems:
            raise SystemExit('The editor’s pages do not match the chapters or the reference list:\n' + '\n'.join(self.problems))

    # ------------------------------------------------------------ narration
    def _check_inline(self, name: str, text: str) -> None:
        for match in CITE.finditer(text):
            for key in match[1].split(','):
                key = key.strip()
                if key not in self.references:
                    self.problems.append(f'narration/{name}: unknown reference "{key}"')
                elif key not in self.cited:
                    self.cited.append(key)
        for match in CHAPTER_LINK.finditer(text):
            if match[1] not in self.chapters:
                self.problems.append(f'narration/{name}: unknown chapter "{match[1]}"')
        for match in INLINE_QUOTE.finditer(text):
            self.quote_targets[(match[1].strip(), match[2])] = self.find_quote(match[1].strip(), match[2], f'narration/{name}')
            self.quoted += 1
        self.narration_words += len(norm_tokens(MARKER.sub('', text)))

    def _parse_narration(self, name: str, text: str) -> list[tuple]:
        """Editor's writing. '> [chapter-slug] words' quotes Steven and must be found in that chapter."""
        parsed: list[tuple] = []
        for block in blocks_of(text):
            flat = ' '.join(line.strip() for line in block.split('\n'))
            quote = STEVEN_QUOTE.fullmatch(flat)
            if quote:
                target = self.find_quote(quote[1].strip(), quote[2].strip(), f'narration/{name}')
                parsed.append(('quote', quote[1].strip(), quote[2].strip(), target))
                self.quoted += 1
            elif block.startswith('## '):
                parsed.append(('h', block[3:].strip()))
                self._check_inline(name, block)
            elif re.match(r'(-|\d+\.) ', block):
                ordered = block[0].isdigit()
                items = [re.sub(r'^(-|\d+\.) ', '', line.strip()) for line in block.split('\n') if line.strip()]
                parsed.append(('ol' if ordered else 'ul', items))
                self._check_inline(name, block)
            else:
                parsed.append(('p', flat))
                self._check_inline(name, flat)
        return parsed

    def ninline(self, text: str, href: Href) -> str:
        """Editor's prose. {q:chapter|words} quotes Steven (verified), {cite:key} cites a source, {ch:chapter} links a chapter."""
        out: list[str] = []
        for piece in MARKER.split(text):
            quote, cite, link = INLINE_QUOTE.fullmatch(piece), CITE.fullmatch(piece), CHAPTER_LINK.fullmatch(piece)
            if quote:
                target = self.quote_targets.get((quote[1].strip(), quote[2]), '')
                out.append(f'<a class="his-words" href="{href(target)}">\u201c{inline(quote[2])}\u201d</a>' if target else inline(quote[2]))
            elif cite:
                links = [f'<a href="{href("ref-" + key.strip())}">{html.escape(self.references[key.strip()]["short"])}</a>'
                         for key in cite[1].split(',') if key.strip() in self.references]
                out.append('(' + '; '.join(links) + (f', {inline(cite[2])}' if cite[2] else '') + ')')
            elif link:
                out.append(f'<a href="{href("chapter-" + link[1][:2])}">{inline(self.chapters[link[1]].title)}</a>'
                           if link[1] in self.chapters else inline(piece))
            else:
                out.append(inline(piece))
        return ''.join(out)

    def narration_html(self, name: str, level: int, href: Href) -> str:
        out: list[str] = []
        for block in self.narration[name]:
            if block[0] == 'h':
                out.append(f'<h{level}>{self.ninline(block[1], href)}</h{level}>')
            elif block[0] == 'p':
                out.append(f'<p>{self.ninline(block[1], href)}</p>')
            elif block[0] in ('ul', 'ol'):
                out.append(f'<{block[0]}>' + ''.join(f'<li>{self.ninline(item, href)}</li>' for item in block[1]) + f'</{block[0]}>')
            else:
                _kind, slug, text, target = block
                title = inline(self.chapters[slug].title) if slug in self.chapters else slug
                out.append(f'<blockquote class="steven-quote"><p>{inline(text)}</p>'
                           f'<p class="guide-cite">Steven, <a href="{href(target)}">{title}</a></p></blockquote>')
        return '\n'.join(out)

    def narrator_box(self, name: str, label: str, level: int, href: Href) -> str:
        if name not in self.narration:
            return ''
        return (f'<div class="narrator"><p class="narrator-label">{html.escape(self.config["editor"])} · {html.escape(label)}</p>\n'
                f'{self.narration_html(name, level, href)}\n</div>')

    # ------------------------------------------------------------ structure
    def number(self, slug: str) -> str:
        return slug[:2]

    def stats(self, slug: str) -> dict:
        chapter = self.chapters[slug]
        result = {}
        for source_id in dict.fromkeys(p.source for p in chapter.passages):
            source = self.sources[source_id]
            kept = {i for p in chapter.passages if p.source == source_id for i in p.kept}
            speakers = {}
            for speaker in sorted({t.speaker or 'All speakers' for t in source.tokens}):
                total = sum((t.speaker or 'All speakers') == speaker for t in source.tokens)
                mine = sum((source.tokens[i].speaker or 'All speakers') == speaker for i in kept)
                speakers[speaker] = {'kept': mine, 'transcribed': total}
            result[source_id] = speakers
        return result

    def find_quote(self, slug: str, quote: str, what: str) -> str:
        chapter = self.chapters.get(slug)
        if chapter is None:
            self.problems.append(f'{what}: unknown chapter {slug}')
            return ''
        hits = [p for p in chapter.passages if quote in p.text.replace('\n', ' ')]
        if not hits:
            wanted = ' '.join(norm_tokens(quote))
            near = [p for p in chapter.passages if wanted in ' '.join(norm_tokens(p.text))]
            if near:
                self.problems.append(f'{what}: quote differs in punctuation from {near[0].id}: "{quote[:70]}"')
            else:
                self.problems.append(f'{what}: quote not found in {slug}: "{quote[:70]}"')
            return ''
        return hits[0].id

    def find_block(self, slug: str, block: str, what: str) -> str:
        chapter = self.chapters.get(slug)
        if chapter is None:
            self.problems.append(f'{what}: unknown chapter {slug}')
            return ''
        number = int(block[1:])
        later = [p for p in chapter.passages if int(p.block_id[1:]) >= number]
        if not later:
            self.problems.append(f'{what}: no passage at or after {block} in {slug}')
            return ''
        return later[0].id

    def _sections(self) -> list[Section]:
        config = self.config
        sections: list[Section] = []
        if 'preface' in self.narration:
            sections.append(Section('editors-preface', 'front', 'Editor’s preface', 'preface.xhtml',
                                    lambda level, href, item: f'<h{level} id="editors-preface">Editor’s preface</h{level}>\n'
                                    f'<p class="chapter-subtitle">{html.escape(config["editor"])}</p>\n'
                                    f'<div class="narrator-essay">{self.narration_html("preface", level + 1, href)}</div>',
                                    ['editors-preface']))
        sections.append(Section('about-this-edition', 'front', 'How this book was made', 'about.xhtml',
                                lambda level, href, item: f'<h{level} id="about-this-edition">How this book was made</h{level}>\n'
                                + prose(self.editorial['about'], level + 1), ['about-this-edition']))
        index = 0
        for part_number, part in enumerate(config['parts'], 1):
            if part.get('title'):
                anchor = f'part-{part_number}'
                label = f'Part {ORDINALS[index]}'
                index += 1
                title = part['title']
                intro = part.get('intro', '')

                def render_part(level, href, item, anchor=anchor, label=label, title=title, intro=intro):
                    body = f'<h{level} id="{anchor}" class="part"><span class="part-label">{label}</span> {inline(title)}</h{level}>'
                    return body + (f'\n<p class="part-intro">{inline(intro)}</p>' if intro else '')
                sections.append(Section(anchor, 'part', f'{label}: {title}', f'{anchor}.xhtml', render_part, [anchor]))
            for slug in part.get('chapters', []):
                chapter = self.chapters[slug]
                number = self.number(slug)
                anchors = [f'chapter-{number}'] + [p.id for p in chapter.passages]

                def render_chapter(level, href, item, chapter=chapter, number=number, slug=slug):
                    out = [f'<h{level} id="chapter-{number}">{inline(chapter.title)}</h{level}>']
                    if chapter.subtitle:
                        out.append(f'<p class="chapter-subtitle">{inline(chapter.subtitle)}</p>')
                    out.append(self.narrator_box(f'before-{slug}', 'before you read', level + 1, href))
                    out.append(chapter_passages(chapter, level))
                    out.append(self.narrator_box(f'after-{slug}', 'connections and questions', level + 1, href))
                    return '\n'.join(piece for piece in out if piece)
                sections.append(Section(f'chapter-{number}', 'chapter', chapter.title, f'ch{number}.xhtml', render_chapter, anchors))
            for essay in part.get('essays', []):
                name, title = essay['file'], essay['title']
                anchor = 'essay-' + name
                if name not in self.narration:
                    self.problems.append(f'book.json: essay "{name}" has no narration/{name}.txt')
                    continue

                def render_essay(level, href, item, name=name, title=title, anchor=anchor):
                    return (f'<h{level} id="{anchor}">{inline(title)}</h{level}>\n'
                            f'<p class="chapter-subtitle">{html.escape(config["editor"])}</p>\n'
                            f'<div class="narrator-essay">{self.narration_html(name, level + 1, href)}</div>')
                sections.append(Section(anchor, 'essay', title, f'{anchor}.xhtml', render_essay, [anchor]))
        sections.append(self._guide())
        if self.cited:
            sections.append(self._works())
        sections.append(self._sources())
        return sections

    def _guide(self) -> Section:
        guide = self.guide
        teachings = [(group, [(entry, self.find_quote(entry['chapter'], entry['quote'], 'guide teaching')) for entry in group['entries']])
                     for group in guide['teachings']]
        practices = [(entry, self.find_block(entry['chapter'], entry['block'], 'guide practice')) for entry in guide['practices']]
        experiences = [(entry, self.find_block(entry['chapter'], entry['block'], 'guide experience')) for entry in guide['experiences']]
        anchors = ['readers-guide', 'guide-teachings', 'guide-practices', 'guide-experiences']

        def by_chapter(entries, level, href, text):
            out: list[str] = []
            current = None
            rows: list[str] = []
            for entry, target in entries:
                if entry['chapter'] != current:
                    if rows:
                        out.append('<ul class="guide-list">' + ''.join(rows) + '</ul>')
                        rows = []
                    current = entry['chapter']
                    out.append(f'<h{level}>{inline(self.chapters[current].title)}</h{level}>')
                when = f' <span class="guide-when">({inline(entry["when"])})</span>' if entry.get('when') else ''
                rows.append(f'<li><a href="{href(target)}">{inline(entry[text])}</a>{when}</li>')
            if rows:
                out.append('<ul class="guide-list">' + ''.join(rows) + '</ul>')
            return out

        def render(level, href, item):
            out = [f'<h{level} id="readers-guide">A reader’s guide</h{level}>', prose(guide['intro'], level + 1),
                   f'<h{level + 1} id="guide-teachings">In his words</h{level + 1}>',
                   prose(guide['teachings_intro'], level + 2)]
            for group, entries in teachings:
                out.append(f'<h{level + 2}>{inline(group["heading"])}</h{level + 2}>')
                for entry, target in entries:
                    out.append(f'<blockquote class="guide-quote"><p>{inline(entry["quote"])}</p><p class="guide-cite">'
                               f'<a href="{href(target)}">{inline(self.chapters[entry["chapter"]].title)}</a></p></blockquote>')
            out.append(f'<h{level + 1} id="guide-practices">How to try it yourself</h{level + 1}>')
            out.append(prose(guide['practices_intro'], level + 2))
            out.extend(by_chapter(practices, level + 2, href, 'name'))
            out.append(f'<h{level + 1} id="guide-experiences">The experiences he recounts</h{level + 1}>')
            out.append(prose(guide['experiences_intro'], level + 2))
            out.extend(by_chapter(experiences, level + 2, href, 'label'))
            return '\n'.join(out)
        return Section('readers-guide', 'back', 'A reader’s guide', 'guide.xhtml', render, anchors)

    def _works(self) -> Section:
        cited = sorted((self.references[key] for key in self.cited), key=lambda ref: (ref['authors'].lower(), ref['year']))

        def render(level, href, item):
            out = [f'<h{level} id="works-cited">Works cited</h{level}>', prose(self.editorial['works'], level + 1), '<ul class="works">']
            for ref in cited:
                where = f' {inline(ref["container"])}.' if ref.get('container') else ''
                title = f'<em>{inline(ref["title"])}</em>' if ref.get('kind') in ('book', 'report', 'podcast') else f'“{inline(ref["title"])}”'
                link = f' <a href="{html.escape(ref["url"])}">{html.escape(ref["url"])}</a>' if ref.get('url') else ''
                out.append(f'<li id="ref-{ref["key"]}">{inline(ref["authors"])}. {html.escape(ref["year"])}. {title}.{where}{link}</li>')
            out.append('</ul>')
            return '\n'.join(out)
        return Section('works-cited', 'back', 'Works cited', 'works.xhtml', render, ['works-cited'] + [f'ref-{ref["key"]}' for ref in cited])

    def _sources(self) -> Section:
        config = self.config
        slugs = [slug for part in config['parts'] for slug in part.get('chapters', [])]

        def render(level, href, item):
            out = [f'<h{level} id="sources-and-editorial-note">Sources and editorial note</h{level}>',
                   prose(self.editorial['sources'], level + 1)]
            for slug in slugs:
                chapter = self.chapters[slug]
                number = self.number(slug)
                out.append(f'<h{level + 1} id="source-{number}">{inline(chapter.title)}</h{level + 1}>')
                note = config.get('chapter_notes', {}).get(slug, '')
                if note:
                    out.append(f'<p>{inline(note)}</p>')
                for source_id, speakers in self.stats(slug).items():
                    meta = config['sources'][source_id]
                    passages = [p for p in chapter.passages if p.source == source_id]
                    first = min(self.sources[source_id].tokens[p.kept[0]].time for p in passages)
                    last = max(self.sources[source_id].tokens[p.kept[-1]].time for p in passages)
                    dated = f'{meta["date"]} ({meta["date_basis"].lower()})' if meta.get('date') else meta['date_basis'].lower()
                    counts = '; '.join(f'{name}: {c["kept"]:,} of {c["transcribed"]:,} transcribed words'
                                       for name, c in speakers.items() if c['kept'])
                    out.append(f'<p class="source-line"><em>{inline(meta["title"])}</em>'
                               f'{" (" + inline(meta["show"]) + ")" if meta.get("show") else ""}. {inline(dated[0].upper() + dated[1:])}. '
                               f'Passages fall within {clock(first)}–{clock(last)} of the recording. Retained: {counts}. '
                               f'<a href="{item(meta["item"])}">Recording and full transcript in the archive</a>.</p>')
                out.append(f'<p class="source-return"><a href="{href("chapter-" + number)}">Return to chapter</a></p>')
            out.append(prose(self.editorial['sources-end'], level + 1))
            return '\n'.join(out)
        anchors = ['sources-and-editorial-note'] + [f'source-{self.number(slug)}' for slug in slugs]
        return Section('sources-and-editorial-note', 'back', 'Sources and editorial note', 'sources.xhtml', render, anchors)

    # --------------------------------------------------------------- output
    def toc(self, href: Href) -> str:
        out = ['<ul>']
        open_part = False
        for section in self.sections:
            if section.kind == 'part':
                if open_part:
                    out.append('</ul></li>')
                out.append(f'<li class="toc-part"><a href="{href(section.id)}">{inline(section.title)}</a><ul>')
                open_part = True
            else:
                if open_part and section.kind == 'back':
                    out.append('</ul></li>')
                    open_part = False
                out.append(f'<li><a href="{href(section.id)}">{inline(section.title)}</a></li>')
        if open_part:
            out.append('</ul></li>')
        out.append('</ul>')
        return ''.join(out)

    def totals(self) -> dict:
        passages = [p for chapter in self.chapters.values() for p in chapter.passages]
        return {'chapters': len(self.chapters), 'passages': len(passages),
                'words': sum(len(p.kept) for p in passages), 'editor_words': self.narration_words}

    def body(self, level: int, href: Href, item: Callable[[str], str]) -> str:
        return '\n'.join(section.render(level, href, item) for section in self.sections)


STYLE = '''body { font-family: Georgia, "Times New Roman", serif; line-height: 1.65; margin: 6%; }
p { margin: 0 0 1em; orphans: 3; widows: 3; }
h1,h2,h3,h4 { font-weight: normal; line-height: 1.2; page-break-after: avoid; }
h1 { font-size: 2.1em; margin: 2em 0 1em; }
h2 { font-size: 1.3em; margin: 2em 0 1em; }
h3 { font-size: 1.1em; margin: 1.8em 0 .8em; font-style: italic; }
h4 { font-size: 1em; margin: 1.6em 0 .6em; font-weight: bold; }
a { color: inherit; }
.titlepage { text-align: center; margin-top: 20%; }
.title { font-size: 2.7em; margin-bottom: .3em; }
.subtitle { font-size: 1.2em; }
.author { margin-top: 2em; font-size: 1.25em; }
.with, .edition-line { font-size: .95em; }
.epigraph { margin: 3.5em 8% 0; font-style: italic; border: 0; padding: 0; }
.part { text-align: center; margin: 4em 0 1.2em; page-break-before: always; }
.part-label { display: block; font-size: .5em; letter-spacing: .2em; text-transform: uppercase; margin-bottom: .8em; }
.part-intro { text-align: center; font-style: italic; margin-bottom: 3em; }
.chapter-subtitle { font-style: italic; margin-top: -1em; margin-bottom: 2.5em; }
.speaker { font-variant: small-caps; font-weight: bold; letter-spacing: .04em; }
.verse p { margin: 1.5em 0 1.5em 1.5em; line-height: 1.9; }
.editor-note { font-size: .92em; font-style: italic; margin: 1.5em 1.5em; }
.editor-note strong { font-style: normal; }
.narrator { font-family: Helvetica, Arial, sans-serif; font-size: .9em; line-height: 1.6; margin: 2.5em 0; padding: .2em 0 .2em 1.1em; border-left: 3px solid #888; }
.narrator-essay { font-family: Helvetica, Arial, sans-serif; font-size: .95em; line-height: 1.65; }
.narrator-label { font-size: .78em; letter-spacing: .14em; text-transform: uppercase; font-weight: bold; margin-bottom: 1em; }
.narrator h2, .narrator h3, .narrator-essay h2, .narrator-essay h3 { font-family: Helvetica, Arial, sans-serif; font-style: normal; font-weight: bold; font-size: 1.05em; }
.his-words { text-decoration: none; font-family: Georgia, "Times New Roman", serif; }
blockquote.steven-quote { font-family: Georgia, "Times New Roman", serif; font-size: 1.08em; margin: 1.2em 0 1.4em .6em; padding-left: 1em; border-left: 2px solid #999; }
blockquote.guide-quote { margin: 1.2em 0 1.4em 1.2em; padding-left: 1em; border-left: 2px solid #999; }
.guide-cite { font-size: .85em; font-style: italic; margin-top: -.4em; }
.guide-when { font-size: .9em; font-style: italic; }
.source-line, .source-return, .works li { font-size: .92em; }
.works { list-style: none; padding-left: 0; }
.works li { margin: 0 0 .8em 1.5em; text-indent: -1.5em; word-wrap: break-word; }
nav ul, nav ol { list-style: none; padding-left: 0; }
nav ul ul, nav ol ol { padding-left: 1.2em; margin-top: .6em; }
nav li { margin: 0 0 .6em; }
'''

SCREEN = '''@media screen { body { color:#243333; background:#fcfaf5; } h1,h2,h3,h4 { color:#204c50; } }
@media screen and (min-width:800px) { body { max-width:37em; padding:0 2em; margin:5em auto; font-size:19px; } }
@media (prefers-color-scheme:dark) { body { color:#e4e3dd; background:#1b2829; } h1,h2,h3,h4 { color:#b5ceca; } }
'''

DESCRIPTION = ('Steven Schrembeck’s Reality 101 series in his own words, cut from machine transcripts and checked against them, '
               'with commentary by his friend and editor. AI-assisted; not fully audio-verified or approved by Steven.')


def title_block(config: dict) -> str:
    return (f'<h1 class="title">{inline(config["title"])}</h1>\n<p class="subtitle">{inline(config["subtitle"])}</p>\n'
            f'<p class="author">{inline(config["author"])}</p>\n<p class="with">in conversation with {inline(config["with"])}</p>\n'
            f'<p class="with">Edited and narrated by {inline(config["editor"])}</p>\n'
            f'<p class="edition-line">{inline(config["edition_line"])}</p>\n'
            f'<blockquote class="epigraph"><p>“{inline(config["epigraph"])}”</p></blockquote>')


def standalone(edition: Edition) -> str:
    config = edition.config
    href = lambda target: '#' + target
    item = lambda item_id: f'{ARCHIVE}items/{item_id}.html'
    return f'''<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="author" content="{html.escape(config["author"])}">
<meta name="description" content="{html.escape(DESCRIPTION)}">
<title>{html.escape(config["title"])}: {html.escape(config["subtitle"])}</title>
<style>
{STYLE}{SCREEN}</style>
</head>
<body>
<header id="title-block-header" class="titlepage">
{title_block(config)}
</header>
<nav id="TOC" role="doc-toc">
<h2 id="toc-title">Contents</h2>
{edition.toc(href)}
</nav>
{edition.body(1, href, item)}
</body>
</html>
'''


def render_site(root: Path | None = None) -> dict:
    """Body, contents and facts for the archive website's page (chapters at h2)."""
    edition = Edition()
    href = lambda target: '#' + target
    item = lambda item_id: f'items/{item_id}.html'
    return {'config': edition.config, 'toc': edition.toc(href), 'body': edition.body(2, href, item),
            'epigraph': inline(edition.config['epigraph']),
            'totals': edition.totals(), 'epub': EPUB_NAME}


XHTML = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en-US" xml:lang="en-US">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="../styles/book.css" />
</head>
<body{attrs}>
{body}
</body>
</html>
'''


def epub_bytes(edition: Edition) -> bytes:
    config = edition.config
    where = {anchor: section.file for section in edition.sections for anchor in section.anchors}
    href = lambda target: f'{where[target]}#{target}'
    item = lambda item_id: f'{ARCHIVE}items/{item_id}.html'
    files: list[tuple[str, bytes]] = []
    title = f'{config["title"]}: {config["subtitle"]}'

    def page(name: str, heading: str, body: str, attrs: str = '') -> None:
        text = XHTML.format(title=html.escape(heading), body=body, attrs=attrs)
        ElementTree.fromstring(text.encode('utf-8'))  # well-formed or fail the build
        files.append((f'EPUB/text/{name}', text.encode('utf-8')))

    cover = (BOOK / 'cover.svg').read_text(encoding='utf-8')
    page('cover.xhtml', 'Cover', '<div style="text-align:center"><img src="../media/cover.svg" alt="Cover: '
         + html.escape(title) + '" style="max-width:100%;height:auto" /></div>', ' epub:type="cover"')
    page('title.xhtml', title, f'<section class="titlepage" epub:type="titlepage">\n{title_block(config)}\n</section>')
    kinds = {'front': 'frontmatter', 'part': 'part', 'chapter': 'chapter', 'essay': 'chapter', 'back': 'backmatter'}
    for section in edition.sections:
        page(section.file, section.title, f'<section epub:type="{kinds[section.kind]}">\n{section.render(1, href, item)}\n</section>')

    def nav_items(link: Callable[[Section], str]) -> str:
        out: list[str] = []
        open_part = False
        for section in edition.sections:
            if section.kind == 'part':
                if open_part:
                    out.append('</ol></li>')
                out.append(f'<li>{link(section)}<ol>')
                open_part = True
            else:
                if open_part and section.kind == 'back':
                    out.append('</ol></li>')
                    open_part = False
                out.append(f'<li>{link(section)}</li>')
        if open_part:
            out.append('</ol></li>')
        return ''.join(out)

    nav = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n'
           '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en-US" xml:lang="en-US">\n'
           f'<head><meta charset="utf-8" /><title>{html.escape(title)}</title>'
           '<link rel="stylesheet" type="text/css" href="styles/book.css" /></head>\n<body>\n'
           '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>'
           + nav_items(lambda s: f'<a href="text/{s.file}#{s.id}">{inline(s.title)}</a>')
           + '</ol></nav>\n</body>\n</html>\n')
    ElementTree.fromstring(nav.encode('utf-8'))
    order = 0

    def point(section: Section) -> str:
        nonlocal order
        order += 1
        return (f'<navPoint id="nav-{order}" playOrder="{order}"><navLabel><text>{html.escape(section.title)}</text></navLabel>'
                f'<content src="text/{section.file}#{section.id}" />')
    ncx_points: list[str] = []
    open_part = False
    for section in edition.sections:
        if section.kind == 'part':
            if open_part:
                ncx_points.append('</navPoint>')
            ncx_points.append(point(section))
            open_part = True
        else:
            if open_part and section.kind == 'back':
                ncx_points.append('</navPoint>')
                open_part = False
            ncx_points.append(point(section) + '</navPoint>')
    if open_part:
        ncx_points.append('</navPoint>')
    ncx = ('<?xml version="1.0" encoding="UTF-8"?>\n<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">'
           f'<head><meta name="dtb:uid" content="{config["identifier"]}" /><meta name="dtb:depth" content="2" />'
           '<meta name="dtb:totalPageCount" content="0" /><meta name="dtb:maxPageNumber" content="0" /></head>'
           f'<docTitle><text>{html.escape(title)}</text></docTitle><navMap>{"".join(ncx_points)}</navMap></ncx>\n')
    ElementTree.fromstring(ncx.encode('utf-8'))

    names = ['cover.xhtml', 'title.xhtml'] + [section.file for section in edition.sections]
    ident = lambda name: name.replace('.', '_').replace('-', '_')
    manifest = ''.join(f'<item id="{ident(name)}" href="text/{name}" media-type="application/xhtml+xml" />\n    ' for name in names)
    spine = ''.join(f'<itemref idref="{ident(name)}" />\n    ' for name in names)
    modified = f'{config["compiled"]}T00:00:00Z'
    opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" xml:lang="en-US" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{config["identifier"]}</dc:identifier>
    <dc:title>{html.escape(title)}</dc:title>
    <dc:date>{modified}</dc:date>
    <dc:language>en-US</dc:language>
    <dc:creator id="creator">{html.escape(config["author"])}</dc:creator>
    <meta refines="#creator" property="role" scheme="marc:relators">aut</meta>
    <dc:contributor id="interviewer">{html.escape(config["with"])}</dc:contributor>
    <meta refines="#interviewer" property="role" scheme="marc:relators">ive</meta>
    <dc:contributor id="editor">{html.escape(config["editor"])}</dc:contributor>
    <meta refines="#editor" property="role" scheme="marc:relators">edt</meta>
    <dc:description>{html.escape(DESCRIPTION)}</dc:description>
    <dc:rights>Rights remain with the respective rights holders. Edited from recorded speech, with commentary.</dc:rights>
    <meta name="cover" content="cover_svg" />
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="schema:accessMode">textual</meta>
    <meta property="schema:accessModeSufficient">textual</meta>
    <meta property="schema:accessibilityFeature">readingOrder</meta>
    <meta property="schema:accessibilityFeature">structuralNavigation</meta>
    <meta property="schema:accessibilityFeature">tableOfContents</meta>
    <meta property="schema:accessibilityHazard">none</meta>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="css" href="styles/book.css" media-type="text/css" />
    <item id="cover_svg" href="media/cover.svg" media-type="image/svg+xml" properties="cover-image" />
    {manifest}</manifest>
  <spine toc="ncx">
    {spine}</spine>
</package>
'''
    ElementTree.fromstring(opf.encode('utf-8'))
    container = ('<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles></container>\n')
    entries = [('mimetype', b'application/epub+zip'), ('META-INF/container.xml', container.encode()),
               ('EPUB/content.opf', opf.encode('utf-8')), ('EPUB/nav.xhtml', nav.encode('utf-8')),
               ('EPUB/toc.ncx', ncx.encode('utf-8')), ('EPUB/styles/book.css', STYLE.encode('utf-8')),
               ('EPUB/media/cover.svg', cover.encode('utf-8'))] + files
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return buffer.getvalue()


def records(edition: Edition) -> tuple[list[dict], dict]:
    config = edition.config
    slugs = [slug for part in config['parts'] for slug in part.get('chapters', [])]
    passages = []
    corrected: dict[str, int] = {}
    for slug in slugs:
        chapter = edition.chapters[slug]
        for passage in chapter.passages:
            passages.append(passage_record(passage, chapter, edition.sources))
            for index in passage.kept:
                token = edition.sources[passage.source].tokens[index]
                if token.raw.lower() != token.norm:
                    pair = f'{token.raw.lower()} -> {token.norm}'
                    corrected[pair] = corrected.get(pair, 0) + 1
    hashes = {}
    for source_id in sorted({p['source'] for p in passages}):
        path = COLLECTION / config['sources'][source_id]['transcript']
        hashes[config['sources'][source_id]['transcript']] = hashlib.sha256(path.read_bytes()).hexdigest()
    all_passages = [p for chapter in edition.chapters.values() for p in chapter.passages]
    validation = {
        **edition.totals(),
        'sources': len(hashes),
        'all_body_words_match_source_in_order': True,
        'added_body_words': 0,
        'reordered_passages': sum('moved' in p.flags for p in all_passages),
        'speaker_label_overrides': sum('any' in p.flags for p in all_passages),
        'transcript_spellings_corrected': dict(sorted(corrected.items())),
        'retained_words_by_chapter': {slug: edition.stats(slug) for slug in slugs},
        'steven_quotes_in_guide_and_commentary_verified': sum(len(g['entries']) for g in edition.guide['teachings']) + edition.quoted,
        'works_cited': len(edition.cited),
        'review_prompts_open': len(edition.warnings),
        'full_listening_review': False,
        'transcript_sha256': hashes,
    }
    return passages, validation


def build() -> None:
    edition = Edition()
    (BOOK / 'reading.html').write_text(standalone(edition), encoding='utf-8')
    data = epub_bytes(edition)
    (BOOK / EPUB_NAME).write_bytes(data)
    passages, validation = records(edition)
    note = ('Words only; case-insensitive; apostrophes unified; punctuation excluded. Every edited word is retained from '
            'the cited speaker’s transcript in order. "original" is that speaker’s transcript from the first to the last retained word.')
    (BOOK / 'passage-map.json').write_text(json.dumps({'normalization': note, 'passages': passages}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    validation['epub_sha256'] = hashlib.sha256(data).hexdigest()
    (BOOK / 'validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    totals = edition.totals()
    print(f'Built {EPUB_NAME}: {totals["chapters"]} chapters, {totals["passages"]} passages, {totals["words"]} words of the speakers, '
          f'{totals["editor_words"]} words of the editor; {len(edition.cited)} works cited; {len(edition.warnings)} review prompt(s) open')
