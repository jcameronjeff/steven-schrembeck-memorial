"""Create a small static deployment, pinning LFS links to the deployed commit."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
from urllib.parse import unquote, quote
from archive_files import POINTER
from collection_manifest import collect
from contribute import check

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/vercel'
check()
# File metadata is regenerated during every deployment, including for new contributions.
manifest = collect()
ref = os.environ.get('VERCEL_GIT_COMMIT_SHA') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
if not re.fullmatch(r'[a-f0-9]{40}', ref):
    raise ValueError('Expected an immutable Git commit for archive links.')
HOST = f'https://media.githubusercontent.com/media/jcameronjeff/steven-schrembeck-memorial/{ref}/collection/'
lfs = {item['path'] for item in manifest if item['lfs']}
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(ROOT / 'site', OUT, ignore=shutil.ignore_patterns('collection-files', '_worker.js', 'recordings'))
for item in manifest:
    if item['lfs']:
        continue
    target = OUT / 'collection-files' / item['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'collection' / item['path'], target)
selected = {'reality-101-introduction': 'reality/003-trailer-surprise-you-can-learn-how-it-all-works.mp3', 'reverie': 'collected/001-reverie.mp3', 'mortal-steel-trailer': 'collected/012-mortal-steel-trailer.mp3'}
def rewrite(match):
    prefix, raw = match.groups()
    return prefix + HOST + raw if unquote(raw) in lfs else match[0]
for path in OUT.rglob('*.html'):
    if 'collection-files' in path.relative_to(OUT).parts:
        continue
    text = path.read_text()
    text = re.sub(r'((?:href|src)=")(?:\.\./)?collection-files/([^"?]+)', rewrite, text)
    for slug, source in selected.items():
        text = re.sub(r'((?:href|src)=")(?:\.\./)?recordings/' + slug + r'\.mp3', lambda m: m[1] + HOST + quote(source, safe='/'), text)
    text = text.replace('href="downloads/steven-schrembeck-complete.zip" download', 'href="https://github.com/jcameronjeff/steven-schrembeck-memorial/releases/latest"')
    text = text.replace('Download the complete archive ↓', 'Download the latest packaged archive ↗').replace('ZIP64 · Extract, then open START-HERE.html', 'Release snapshots may predate recent contributions; individual files are current.')
    path.write_text(text)
for path in OUT.rglob('*'):
    if path.is_file() and path.stat().st_size < 1024 and POINTER.fullmatch(path.read_bytes()):
        raise ValueError(f'LFS pointer leaked into deployment: {path}')
(OUT / 'downloads/collection-manifest.json').write_text(json.dumps({'files': manifest}, ensure_ascii=False, indent=2) + '\n')
print('Prepared Vercel site:', OUT)
