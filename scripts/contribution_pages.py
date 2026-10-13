"""Publish reviewed contributions without executing source documents."""
import json
from html import escape as e
from urllib.parse import quote
from contribute import validate_metadata


def build_contributions(source, page, head):
    items = []
    for path in sorted((source / 'contributions').glob('*/metadata.json')):
        data = json.loads(path.read_text())
        validate_metadata(data)
        slug = path.parent.name
        rel = f'contributions/{slug}/files/{data["file"]}'
        link = '../collection-files/' + quote(rel, safe='/')
        item = {'id': 'contribution-' + slug, 'title': data['title'], 'kind': 'contribution', 'series': 'Community contributions', 'date': data.get('date', ''), 'path': rel, 'reader': f'items/contribution-{slug}.html', 'origin': data.get('source', ''), 'description': data.get('context', ''), 'size': data['size']}
        original = f'<p><a href="{e(data["source"])}">Original source ↗</a></p>' if data.get('source') else ''
        page(item['reader'], data['title'], head('Community contributions', e(data['title']), 'Shared by ' + e(data['name'])) + f'<div class="prose"><p style="white-space:pre-line">{e(data.get("context", ""))}</p>{original}<p><a class="button" href="{link}" download>Download the preserved file ↓</a></p><p class="source-note">Published with the contributor’s permission. Original file retained with a SHA-256 checksum.</p></div>', 'explore.html', 1)
        items.append(item)
    return items


def build_form(page, head):
    page('contribute.html', 'Share a file or memory', head('Keep the collection growing', 'Something worth keeping.', 'Share a photograph, recording, document, or memory of Steven. Every contribution is reviewed before publication.') + '''
<div class="article-body"><p>Use the invitation link provided by the archive caretaker. Your files stay private while awaiting review. Prefer GitHub? <a href="https://github.com/jcameronjeff/steven-schrembeck-memorial/blob/main/CONTRIBUTING.md">Read the contribution guide ↗</a></p>
<form id="contribution-form" class="contribution-form">
<label for="title">Title</label><input id="title" name="title" required maxlength="200">
<label for="name">Your name or preferred public credit</label><input id="name" name="name" required maxlength="120" autocomplete="name">
<label for="context">The story behind it</label><textarea id="context" name="context" maxlength="4000" rows="4"></textarea>
<label for="date">Date of the original (optional)</label><input id="date" name="date" type="date">
<label for="source">Original web link (optional)</label><input id="source" name="source" type="url" maxlength="2000">
<label for="file">Choose one file (up to 1 GiB)</label><input id="file" name="file" type="file" accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.md,.mp3,.m4a,.wav,.mp4,.mov,.mkv,.webm,.docx">
<label for="memory">Or write a memory</label><textarea id="memory" name="memory" rows="8" maxlength="20000"></textarea>
<label class="consent"><input type="checkbox" name="consent" required> I have permission to share this and agree to its publication in the public archive, with the credit and context above.</label>
<button type="submit" class="button">Send for review</button></form>
<p id="upload-status" role="status" aria-live="polite"></p><noscript><p>Uploads require JavaScript. You can also share a file directly with the archive caretaker.</p></noscript></div>
<style>.contribution-form{display:grid;gap:12px}.contribution-form input,.contribution-form textarea{font:inherit;padding:10px;max-width:100%;border:1px solid #aaa;border-radius:4px}.contribution-form label{margin-top:12px}.contribution-form .consent{display:flex;align-items:start;gap:10px}.contribution-form button{justify-self:start;margin-top:16px}.contribution-form[hidden]{display:none}</style>
<script type="module" src="assets/contribute.js"></script>''')
