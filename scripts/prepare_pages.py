"""Make the small GitHub Pages edition; media remains available on OpZero."""
from pathlib import Path
import re, shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/github-pages'
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(ROOT/'site', OUT, ignore=shutil.ignore_patterns('collection-files','_worker.js'))
HOST='https://steven-schrembeck-archive.opzero.sh/'
for p in OUT.rglob('*.html'):
    s=p.read_text()
    s=re.sub(r'((?:href|src)=")(?:\.\./)?collection-files/',r'\1'+HOST+'collection-files/',s)
    s=s.replace('href="downloads/steven-schrembeck-complete.zip"',f'href="{HOST}downloads/steven-schrembeck-complete.zip"')
    p.write_text(s)
print('GitHub Pages edition prepared:', OUT)
