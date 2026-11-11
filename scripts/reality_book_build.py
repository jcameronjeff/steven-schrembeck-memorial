"""Build the Reality 101 reading edition from its checked manuscripts.

Outputs, all in content/reality-101/: reading.html, the EPUB, passage-map.json
and validation.json. The website builder imports render_site() for its page.
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

Href = Callable[[str], str]


@dataclass
class Section:
    id: str            # anchor of its heading
    kind: str          # front | part | chapter | back
    title: str
    file: str          # EPUB file name
    render: Callable[[int, Href, Callable[[str], str]], str]
    anchors: list[str]


def prose(text: str, level: int) -> str:
    """Editorial text: blank-line paragraphs, '## ' subheads, '- ' lists, *emphasis*."""
    out: list[str] = []
    for block in re.split(r'\n\s*\n', text.strip()):
        block = block.strip()
        if block.startswith('## '):
            out.append(f'<h{level}>{inline(block[3:])}</h{level}>')
        elif block.startswith('- '):
            items = ''.join(f'<li>{inline(line[2:].strip())}</li>' for line in block.split('\n'))
            out.append(f'<ul>{items}</ul>')
        else:
            out.append(f'<p>{inline(" ".join(line.strip() for line in block.split(chr(10))))}</p>')
    return '\n'.join(out)


def chapter_body(chapter: Chapter, number: str, level: int) -> str:
    speakers = {passage.speaker for passage in chapter.passages}
    labels = len(speakers) > 1
    out = [f'<h{level} id="chapter-{number}">{inline(chapter.title)}</h{level}>']
    if chapter.subtitle:
        out.append(f'<p class="chapter-subtitle">{inline(chapter.subtitle)}</p>')
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
        self.problems: list[str] = []
        self.sections = self._sections()
        if self.problems:
            raise SystemExit('The reader’s guide does not match the chapters:\n' + '\n'.join(self.problems))

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
        hits = [p for p in chapter.passages if quote in p.text]
        if not hits:
            wanted = norm_tokens(quote)
            hits = [p for p in chapter.passages if ' '.join(wanted) in ' '.join(norm_tokens(p.text))]
            if hits:
                self.problems.append(f'{what}: quote differs in punctuation from {hits[0].id}: "{quote[:70]}"')
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
        sections.append(Section('about-this-edition', 'front', 'About this edition', 'about.xhtml',
                                lambda level, href, item: f'<h{level} id="about-this-edition">About this edition</h{level}>\n'
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
            for slug in part['chapters']:
                chapter = self.chapters[slug]
                number = self.number(slug)
                anchors = [f'chapter-{number}'] + [p.id for p in chapter.passages]
                sections.append(Section(f'chapter-{number}', 'chapter', chapter.title, f'ch{number}.xhtml',
                                        lambda level, href, item, chapter=chapter, number=number: chapter_body(chapter, number, level),
                                        anchors))
        sections.append(self._guide())
        sections.append(self._sources())
        return sections

    def _guide(self) -> Section:
        guide = self.guide
        resolved_teachings = []
        for group in guide['teachings']:
            entries = [(entry, self.find_quote(entry['chapter'], entry['quote'], 'guide teaching')) for entry in group['entries']]
            resolved_teachings.append((group, entries))
        practices = [(entry, self.find_quote(entry['chapter'], entry['quote'], 'guide practice')) for entry in guide['practices']]
        experiences = [(entry, self.find_block(entry['chapter'], entry['block'], 'guide experience')) for entry in guide['experiences']]
        anchors = ['readers-guide', 'guide-teachings', 'guide-practices', 'guide-experiences']

        def cite(entry, target, href):
            return f'<a href="{href(target)}">{inline(self.chapters[entry["chapter"]].title)}</a>'

        def render(level, href, item):
            out = [f'<h{level} id="readers-guide">A reader’s guide</h{level}>', prose(guide['intro'], level + 1),
                   f'<h{level + 1} id="guide-teachings">What he wanted you to know</h{level + 1}>',
                   prose(guide['teachings_intro'], level + 2)]
            for group, entries in resolved_teachings:
                out.append(f'<h{level + 2}>{inline(group["heading"])}</h{level + 2}>')
                for entry, target in entries:
                    out.append(f'<blockquote class="guide-quote"><p>{inline(entry["quote"])}</p>'
                               f'<p class="guide-cite">{cite(entry, target, href)}</p></blockquote>')
            out.append(f'<h{level + 1} id="guide-practices">How to try it yourself</h{level + 1}>')
            out.append(prose(guide['practices_intro'], level + 2))
            for entry, target in practices:
                out.append(f'<div class="guide-practice"><p class="guide-name">{inline(entry["name"])}</p>'
                           f'<blockquote class="guide-quote"><p>{inline(entry["quote"])}</p>'
                           f'<p class="guide-cite">{cite(entry, target, href)}</p></blockquote></div>')
            out.append(f'<h{level + 1} id="guide-experiences">The experiences he recounts</h{level + 1}>')
            out.append(prose(guide['experiences_intro'], level + 2))
            current = None
            rows: list[str] = []
            for entry, target in experiences:
                if entry['chapter'] != current:
                    if rows:
                        out.append('<ul class="guide-list">' + ''.join(rows) + '</ul>')
                        rows = []
                    current = entry['chapter']
                    out.append(f'<h{level + 2}>{inline(self.chapters[current].title)}</h{level + 2}>')
                when = f' <span class="guide-when">({inline(entry["when"])})</span>' if entry.get('when') else ''
                rows.append(f'<li><a href="{href(target)}">{inline(entry["label"])}</a>{when}</li>')
            if rows:
                out.append('<ul class="guide-list">' + ''.join(rows) + '</ul>')
            return '\n'.join(out)
        return Section('readers-guide', 'back', 'A reader’s guide', 'guide.xhtml', render, anchors)

    def _sources(self) -> Section:
        config = self.config

        def render(level, href, item):
            out = [f'<h{level} id="sources-and-editorial-note">Sources and editorial note</h{level}>',
                   prose(self.editorial['sources'], level + 1)]
            for part in config['parts']:
                for slug in part['chapters']:
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
        anchors = ['sources-and-editorial-note'] + [f'source-{self.number(slug)}' for part in config['parts'] for slug in part['chapters']]
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
                'words': sum(len(p.kept) for p in passages)}

    def body(self, level: int, href: Href, item: Callable[[str], str]) -> str:
        return '\n'.join(section.render(level, href, item) for section in self.sections)


STYLE = '''body { font-family: Georgia, "Times New Roman", serif; line-height: 1.65; margin: 6%; }
p { margin: 0 0 1em; orphans: 3; widows: 3; }
h1,h2,h3 { font-weight: normal; line-height: 1.2; page-break-after: avoid; }
h1 { font-size: 2.1em; margin: 2em 0 1em; }
h2 { font-size: 1.3em; margin: 2em 0 1em; }
h3 { font-size: 1.1em; margin: 1.8em 0 .8em; font-style: italic; }
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
.editor-note { font-size: .92em; font-style: italic; margin: 1.5em 1.5em; }
.editor-note strong { font-style: normal; }
blockquote.guide-quote { margin: 1.2em 0 1.4em 1.2em; padding-left: 1em; border-left: 2px solid #999; }
.guide-cite { font-size: .85em; font-style: italic; margin-top: -.4em; }
.guide-name { font-weight: bold; margin-bottom: .2em; }
.guide-when { font-size: .9em; font-style: italic; }
.source-line, .source-return { font-size: .92em; }
nav ul, nav ol { list-style: none; padding-left: 0; }
nav ul ul, nav ol ol { padding-left: 1.2em; margin-top: .6em; }
nav li { margin: 0 0 .6em; }
'''

SCREEN = '''@media screen { body { color:#243333; background:#fcfaf5; } h1,h2,h3 { color:#204c50; } }
@media screen and (min-width:800px) { body { max-width:37em; padding:0 2em; margin:5em auto; font-size:19px; } }
@media (prefers-color-scheme:dark) { body { color:#e4e3dd; background:#1b2829; } h1,h2,h3 { color:#b5ceca; } }
'''

DESCRIPTION = ('A source-based, AI-assisted reading edition of recorded speech. No new first-person prose. '
               'Compared with machine transcripts; not fully audio-verified or approved by Steven.')


def title_block(config: dict) -> str:
    return (f'<h1 class="title">{inline(config["title"])}</h1>\n<p class="subtitle">{inline(config["subtitle"])}</p>\n'
            f'<p class="author">{inline(config["author"])}</p>\n<p class="with">in conversation with {inline(config["with"])}</p>\n'
            f'<p class="edition-line">{inline(config["edition_line"])}</p>\n'
            f'<blockquote class="epigraph"><p>\u201c{inline(config["epigraph"])}\u201d</p></blockquote>')


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
    for section in edition.sections:
        kind = {'front': 'frontmatter', 'part': 'part', 'chapter': 'chapter', 'back': 'backmatter'}[section.kind]
        page(section.file, section.title, f'<section epub:type="{kind}">\n{section.render(1, href, item)}\n</section>')

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
    manifest = ''.join(f'<item id="{name.replace(".", "_").replace("-", "_")}" href="text/{name}" media-type="application/xhtml+xml" />\n    '
                       for name in names)
    spine = ''.join(f'<itemref idref="{name.replace(".", "_").replace("-", "_")}" />\n    ' for name in names)
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
    <dc:contributor id="contributor">{html.escape(config["with"])}</dc:contributor>
    <meta refines="#contributor" property="role" scheme="marc:relators">ive</meta>
    <dc:description>{html.escape(DESCRIPTION)}</dc:description>
    <dc:rights>Rights remain with the respective rights holders. Edited from recorded speech.</dc:rights>
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
    passages = []
    corrected: dict[str, int] = {}
    for part in config['parts']:
        for slug in part['chapters']:
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
        'name_spellings_corrected': dict(sorted(corrected.items())),
        'retained_words_by_chapter': {slug: edition.stats(slug) for part in config['parts'] for slug in part['chapters']},
        'guide_quotes_verified': sum(len(g['entries']) for g in edition.guide['teachings']) + len(edition.guide['practices']),
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
    print(f'Built {EPUB_NAME}: {totals["chapters"]} chapters, {totals["passages"]} passages, {totals["words"]} words; '
          f'{len(edition.warnings)} review prompt(s) open')
