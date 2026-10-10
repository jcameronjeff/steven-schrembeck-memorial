"""A complete, progressively enhanced listening library from the archive catalogue."""
from datetime import datetime
from html import escape as e


def publication_label(item):
    if not item.get('date'):
        return 'Publication date unknown'
    date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%B %-d, %Y')
    return 'Published ' + date


def audio_library(items, archive_url, size_label):
    audio = [item for item in items if item['kind'] == 'audio']
    saved = sum(bool(item.get('path')) for item in audio)
    groups = [
        ('reality', 'Reality 101', 'Personal journals, questions, and explorations.', 'reality'),
        ('collected', 'Collected', 'Audio fiction, imagined worlds, and conversations about making them.', 'collected'),
        ('guests', 'Guest appearances', 'Steven in conversation on other podcasts.', None),
        ('adaptations', 'Adaptations', 'His stories, performed by other storytellers.', None),
    ]
    sections = []
    options = ['<option value="all">All series</option>']
    for key, title, description, cover in groups:
        episodes = [item for item in audio if (item['series'].startswith('Adaptations') if key == 'adaptations' else item['series'] == title)]
        # Keep episodes in publication order, with the introduction first in Reality 101.
        episodes.sort(key=lambda item: (not (key == 'reality' and 'trailer' in item['id']), item['date'] or '9999', item['title']))
        options.append(f'<option value="{key}">{e(title)} ({len(episodes)})</option>')
        rows = []
        for item in episodes:
            reader = item.get('reader') or 'items/' + item['id'] + '.html'
            links = []
            if item.get('transcript'):
                links.append(f'<a href="{reader}#transcript">Read transcript</a>')
            else:
                links.append(f'<a href="{reader}">Recording details</a>')
            if item.get('origin'):
                links.append(f'<a href="{e(item["origin"])}">Original source ↗</a>')
            if item.get('path'):
                local = archive_url(item['path'])
                player = f'<audio controls preload="none" aria-label="{e(item["title"])}"><source src="{local}" type="audio/mpeg"></audio>'
                links.append(f'<a href="{local}?download=1" download>Download MP3 · {size_label(item["size"])} ↓</a>')
                availability = ''
                action = 'Listen'
            else:
                player = f'<p class="listen-external">No saved audio file. <a href="{e(item["origin"])}">Listen at the original source ↗</a></p>'
                availability = '<span class="listen-badge">Original link only</span>'
                action = 'View links'
            credit = f'<p class="listen-credit">{e(item["series"])} · A performance of <em>An Unwelcome Audience</em>.</p>' if key == 'adaptations' else ''
            search = e(' '.join([item['title'], item['series'], item['date'], publication_label(item)]))
            rows.append(f'''<details class="listen-item" data-entry data-kind="{key}" data-search-text="{search}">
<summary><span class="listen-title">{e(item['title'])}{availability}</span><span class="listen-meta"><span>{e(item.get('duration', ''))}</span><span>{publication_label(item)}</span></span><span class="listen-toggle">{action} <span aria-hidden="true">+</span></span></summary>
<div class="listen-body">{credit}{player}<div class="listen-links">{''.join(links)}</div></div></details>''')
        artwork = f'<img src="assets/{cover}-cover.jpg" alt="" width="68" height="68" loading="lazy">' if cover else ''
        count = f'{len(episodes)} recordings' if key != 'adaptations' else '1 saved · 1 original link'
        sections.append(f'<section class="listen-group" data-entry-group aria-labelledby="listen-{key}"><header class="listen-group-head">{artwork}<div><p class="eyebrow">{count}</p><h3 id="listen-{key}">{e(title)}</h3><p>{description}</p></div></header><div class="listen-list">'+''.join(rows)+'</div></section>')
    return f'''<section id="listen" class="listening-library" aria-labelledby="listen-title"><div class="section-heading"><div><p class="eyebrow">Listen, and linger</p><h2 id="listen-title">His voice. His imagination.</h2><p class="listen-intro">All {saved} saved recordings, with one further performance linked at its source. Choose a title to open its player, transcript, and download links.</p></div></div>
<div class="searchbar js-only"><label class="visually-hidden" for="listen-search">Search recordings</label><input class="search-input" id="listen-search" type="search" placeholder="Find a story, episode, or conversation…" data-search><select aria-label="Filter recordings by series" data-kind-select>{''.join(options)}</select></div>
<div class="listen-toolbar"><p class="results-status" data-results data-noun="recordings" role="status">{len(audio)} recordings</p><p>Publication order within each series · Recording dates unknown</p></div>
<noscript><p class="noscript-note">All recordings are listed below. Open a title to listen, or use your browser’s Find feature to search.</p></noscript>
{''.join(sections)}<div class="empty-state" data-empty hidden><h3>No matching recordings.</h3><p>Try another title or choose a different series.</p><button class="button secondary" data-reset>Show all recordings</button></div>
<p class="source-note">Dates are publication dates reported by the podcast feeds, not recording dates. Saved audio plays directly from the archive. Machine transcripts are unreviewed and may contain errors. <a href="files.html?type=audio">Browse all audio downloads →</a></p></section>'''
