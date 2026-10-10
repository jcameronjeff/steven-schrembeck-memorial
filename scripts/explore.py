"""One browsing experience for all catalogued works."""
from html import escape as e
from listening import publication_label


def explore_library(items, articles, archive_url):
    descriptions = {article['slug']: article['description'] for article in articles}
    series = sorted({item['series'].split(' · ')[0] for item in items})
    kinds = [('all', 'Everything'), ('writing', 'Writing'), ('audio', 'Audio'),
             ('video', 'Video'), ('talk', 'Presentations'), ('book', 'Books')]
    buttons = ''.join(
        f'<button class="filter-button" data-filter="{kind}" aria-pressed="{str(kind == "all").lower()}">{label} '
        f'<span>{len(items) if kind == "all" else sum(item["kind"] == kind for item in items)}</span></button>'
        for kind, label in kinds)
    options = ''.join(f'<option value="{e(name)}">{e(name)}</option>' for name in series)
    rows = []
    for item in items:
        reader = item.get('reader') or ('items/' + item['id'] + '.html'
                  if item['kind'] != 'writing' else archive_url(item['path']))
        collection = item['series'].split(' · ')[0]
        description = item.get('description') or descriptions.get(item['id'], '')
        date = publication_label(item) if item['kind'] == 'audio' else item['date'] or 'Date not established'
        if item.get('edition'):
            date = 'Compiled ' + item['date']
        elif item['kind'] == 'writing':
            date = 'Created ' + item['date']
        elif item['kind'] == 'video':
            date = 'Uploaded ' + item['date']
        elif item['kind'] == 'talk':
            date = 'Recorded ' + item['date']
        note = ''
        if item.get('unpublished'):
            note = 'Source marked Unpublished · preserved text'
        elif item.get('edition'):
            note = 'Edited reading edition · 10 chapters'
        elif not item.get('path'):
            note = 'Original links only · no saved copy'
        elif collection == 'Adaptations':
            note = 'A performance of An Unwelcome Audience'
        search = e(' '.join([item['title'], item['series'], item['date'], date, description, note]))
        metadata = e(date) + (f' · {e(item["duration"])}' if item.get('duration') else '')
        extra = f'<p class="explore-description">{e(description)}</p>' if description else ''
        if note:
            extra += f'<p class="catalog-note">{e(note)}</p>'
        action = {'writing': 'Read', 'video': 'Watch & explore', 'talk': 'Watch presentation',
                  'book': 'Explore the book', 'audio': 'Listen at source'}[item['kind']]
        if item.get('edition'):
            action = 'Read the book'
        if item['kind'] == 'audio' and item.get('path'):
            content = f'''<details class="explore-player"><summary>Listen <span aria-hidden="true">+</span></summary>
<audio controls preload="none" aria-label="{e(item['title'])}"><source src="{archive_url(item['path'])}" type="audio/mpeg"></audio>
<p><a href="{reader}{'#transcript' if item.get('transcript') else ''}">{'Read transcript' if item.get('transcript') else 'Recording details'} →</a></p></details>'''
        else:
            content = f'<a class="text-link explore-action" href="{reader}">{action} →</a>'
        rows.append(f'''<article class="explore-item" data-entry data-kind="{item['kind']}" data-series="{e(collection)}" data-date="{item['date']}" data-title="{e(item['title'])}" data-search-text="{search}">
<div class="explore-copy"><p class="eyebrow">{e(item['series'])}</p><h2><a href="{reader}">{e(item['title'])}</a></h2><p class="explore-meta">{metadata}</p>{extra}</div>{content}</article>''')
    return f'''<div class="explore-controls js-only">
<div class="filter-buttons" role="group" aria-label="Content type">{buttons}</div>
<div class="searchbar"><div class="explore-search"><label for="explore-search">Search the collection</label><input class="search-input" type="search" id="explore-search" placeholder="Find a title, idea, or year…" data-search></div>
<div><label for="explore-series">Collection</label><select id="explore-series" data-series-select><option value="all">All collections</option>{options}</select></div>
<div><label for="explore-sort">Sort by</label><select id="explore-sort" data-sort-select><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="title">Title A–Z</option></select></div></div></div>
<div class="catalog-toolbar"><p class="results-status" data-results data-noun="works" role="status">{len(items)} works</p><a class="text-link" href="files.html">Keep a copy →</a></div>
<noscript><p class="noscript-note">All works are listed below, newest first. Use your browser’s Find feature to search; open an audio player to listen.</p></noscript>
<div class="explore-list" data-sort-list>{''.join(rows)}</div>
<div class="empty-state" data-empty hidden><h2>No matching works.</h2><p>Try another word or choose a different collection.</p><button class="button secondary" data-reset>Show everything</button></div>
<p class="source-note">Audio dates are publication dates from the saved feeds, not recording dates. Video dates are upload dates; writing uses the source’s “Created time.” Presentation dates come from recording metadata. Original sources and transcripts are available on each work’s page.</p>'''
