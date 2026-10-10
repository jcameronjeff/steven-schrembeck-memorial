"""Make an independent Pages edition using GitHub's own LFS media URLs."""
from pathlib import Path
import re, shutil, json
from urllib.parse import quote,unquote

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/github-pages'
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(ROOT/'site', OUT, ignore=shutil.ignore_patterns('collection-files','_worker.js'))
HOST='https://media.githubusercontent.com/media/jcameronjeff/steven-schrembeck-memorial/main/collection/'
manifest=json.loads((ROOT/'collection-manifest.json').read_text())['files']
lfs={item['path'] for item in manifest if item['lfs']}
for item in manifest:
    if item['path'] in lfs: continue
    target=OUT/'collection-files'/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'collection'/item['path'],target)
def media_link(match):
    prefix,raw=match.groups()
    return prefix+HOST+raw if unquote(raw) in lfs else match[0]
for p in OUT.rglob('*.html'):
    if 'collection-files' in p.relative_to(OUT).parts: continue
    s=p.read_text()
    s=re.sub(r'((?:href|src)=")(?:\.\./)?collection-files/([^"?]+)',media_link,s)
    s=s.replace('href="downloads/steven-schrembeck-complete.zip" download','href="https://github.com/jcameronjeff/steven-schrembeck-memorial/releases/tag/archive-2026-10-10"')
    s=s.replace('Download the complete archive ↓','Download the archive ZIP parts ↗')
    s=s.replace('ZIP64 · Extract, then open START-HERE.html','Extract all ZIP parts into one folder, then open START-HERE.html')
    p.write_text(s)
print('GitHub Pages edition prepared:', OUT)
