"""Publish the compiled books without editing their prose."""
import re
import shutil

from reality_book_build import render_site

TITLE = 'The Small Moments Are Everything'
EPUB = 'the-small-moments-are-everything.epub'
REALITY_PAGE = 'reality-101-book.html'
REALITY_COVER = 'assets/reality-101-book-cover.svg'


def build_book(root, out, page, head):
    source = root / 'content/small-moments'
    shutil.copy2(source / EPUB, out / 'downloads' / EPUB)
    shutil.copy2(source / 'cover.svg', out / 'assets/small-moments-cover.svg')
    comparison = (source / 'source-comparison.html').read_text().replace('href="reading-preview.html', 'href="../book.html')
    (out / 'downloads/book-source-comparison.html').write_text(comparison)
    shutil.copy2(source / 'passage-map.json', out / 'downloads/book-passage-map.json')
    body = (source / 'reading.html').read_text().split('<body>', 1)[1].split('</body>', 1)[0]
    body = re.sub(r'<header id="title-block-header">.*?</header>', '', body, flags=re.S)
    # The site title is the only h1; retain every chapter and passage anchor.
    body = body.replace('<h2', '<h3').replace('</h2>', '</h3>')
    body = body.replace('<h1', '<h2').replace('</h1>', '</h2>')
    body = body.replace('<nav id="TOC" role="doc-toc">', '<nav id="TOC" role="doc-toc" aria-label="Book contents">')
    content = f'''<div class="breadcrumbs book-breadcrumbs"><a href="explore.html?type=book">Explore</a><span>/</span><span>Reading edition</span></div>
<header class="book-head"><img src="assets/small-moments-cover.svg" width="220" height="330" alt="Cover of {TITLE}"><div><p class="eyebrow">A book drawn from the recordings</p><h1>{TITLE}</h1><p class="book-subtitle">Selected recorded reflections on meaning, work, making, and reality.</p><p class="book-byline">Words by Steven Schrembeck · Edited reading edition</p><div class="source-actions"><a class="button" href="#chapter-01">Start reading →</a><a class="text-link" href="downloads/{EPUB}" download>Download EPUB ↓</a></div><p class="small muted">10 chapters · About 18,800 words · Compiled October 10, 2026</p></div></header>
<article class="book-reading prose">{body}<p class="source-note">Explore the editorial record: <a href="downloads/book-source-comparison.html">side-by-side source comparison</a> · <a href="downloads/book-passage-map.json" download>passage map</a>.</p><p class="bottom-link"><a href="#TOC">Back to contents ↑</a></p></article>'''
    page('book.html', TITLE, content, 'explore.html', description='Read The Small Moments Are Everything, an edited collection of Steven Schrembeck’s recorded reflections, or download the EPUB.')
    return {'id': 'the-small-moments-are-everything', 'title': TITLE, 'kind': 'book',
            'series': 'Reading edition', 'date': '2026-10-10', 'edition': True,
            'edition_note': 'Edited reading edition · 10 chapters',
            'reader': 'book.html', 'path': '', 'site_download': 'downloads/' + EPUB,
            'description': 'Ten chapters on meaning, work, attention, learning, making, and reality, selected from his recorded words.'}


def reality_facts(root):
    """The Reality 101 edition, rendered from its checked manuscripts."""
    edition = render_site()
    config, totals = edition['config'], edition['totals']
    rounded = round(totals['words'], -2)
    return {**edition, 'title': config['title'], 'subtitle': config['subtitle'],
            'count': f'{totals["chapters"]} chapters · About {rounded:,} words',
            'compiled': config['compiled']}


def build_reality_book(root, out, page, facts):
    """The series as a book. The page fails to build if any paragraph no longer matches its transcript."""
    source = root / 'content/reality-101'
    title, epub = facts['title'], facts['epub']
    shutil.copy2(source / epub, out / 'downloads' / epub)
    shutil.copy2(source / 'cover.svg', out / REALITY_COVER)
    shutil.copy2(source / 'passage-map.json', out / 'downloads/reality-101-passage-map.json')
    shutil.copy2(source / 'validation.json', out / 'downloads/reality-101-validation.json')
    content = f'''<div class="breadcrumbs book-breadcrumbs"><a href="explore.html?type=book">Explore</a><span>/</span><span>Reading edition</span></div>
<header class="book-head"><img src="{REALITY_COVER}" width="220" height="330" alt="Cover of {title}"><div><p class="eyebrow">The complete series as a book</p><h1>{title}</h1><p class="book-subtitle">{facts['subtitle']}. What happened to him, what he came to understand, and how he said you could try it yourself.</p><p class="book-byline">Words by Steven Schrembeck, in conversation with Joshua Swenson · Edited reading edition</p><div class="source-actions"><a class="button" href="#chapter-00">Start reading →</a><a class="text-link" href="downloads/{epub}" download>Download EPUB ↓</a></div><p class="small muted">{facts['count']} · Compiled November 11, 2026</p></div></header>
<article class="book-reading prose"><blockquote class="book-epigraph"><p>“{facts['epigraph']}”</p></blockquote><nav id="TOC" role="doc-toc" aria-label="Book contents"><h3 id="toc-title">Contents</h3>{facts['toc']}</nav>
{facts['body']}<p class="source-note">Explore the editorial record: <a href="downloads/reality-101-passage-map.json" download>passage map</a> · <a href="downloads/reality-101-validation.json" download>validation record</a>. Every paragraph is checked against its transcript each time this page is built.</p><p class="bottom-link"><a href="#TOC">Back to contents ↑</a></p></article>'''
    page(REALITY_PAGE, title, content, 'explore.html', description='Read Reality 101, Steven Schrembeck’s complete podcast series and earlier conversations as a book in his own words, or download the EPUB.')
    return {'id': 'reality-101-a-journal-of-impossible-experiences', 'title': f'{title}: {facts["subtitle"]}', 'kind': 'book',
            'series': 'Reading edition', 'date': facts['compiled'], 'edition': True,
            'edition_note': f'Edited reading edition · {facts["count"].split(" · ")[0]}',
            'reader': REALITY_PAGE, 'path': '', 'site_download': 'downloads/' + epub,
            'description': 'The complete Reality 101 series, his three audio journals, and selections from earlier interviews, in his own words.'}


def book_download_card(facts):
    return f'''<section class="book-download" aria-labelledby="download-reality-title"><img src="{REALITY_COVER}" alt="" width="115" height="173"><div><p class="eyebrow">The series as a book</p><h2 id="download-reality-title">{facts['title']}</h2><p>{facts['subtitle']}. The complete series, his three audio journals, and selections from earlier interviews, in his own words. An edited reading edition for your e-reader, with the full text also available here on the website.</p><div class="source-actions"><a class="button" href="downloads/{facts['epub']}" download>Download EPUB ↓</a><a class="text-link" href="{REALITY_PAGE}">Read on the web →</a></div></div></section>
<section class="book-download" aria-labelledby="download-book-title"><img src="assets/small-moments-cover.svg" alt="" width="115" height="173"><div><p class="eyebrow">The compiled book</p><h2 id="download-book-title">{TITLE}</h2><p>Ten chapters selected from Steven’s recorded words. An edited reading edition for your e-reader, with the full text also available here on the website.</p><div class="source-actions"><a class="button" href="downloads/{EPUB}" download>Download EPUB ↓</a><a class="text-link" href="book.html">Read on the web →</a></div></div></section>'''
