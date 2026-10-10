"""Create a complete offline ZIP and independent, ordinary ZIP release parts."""
from pathlib import Path
import hashlib,json,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
extra=OUT/'package-extras';extra.mkdir(exist_ok=True)
start=extra/'START-HERE.html'
start.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Steven Schrembeck Archive</title><h1>The Steven Schrembeck Archive</h1><p><a href="index.html">Open the archive website</a></p><p>This copy works offline. Original source links need an internet connection. If you downloaded the GitHub release parts, extract all of them into this same folder first.</p></html>')
files=[]
for base,prefix in [(ROOT/'site',''),(ROOT/'collection','collection-files/')]:
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.is_symlink() or p.name in {'_worker.js','.DS_Store'} or 'collection-files' in p.relative_to(base).parts: continue
        files.append((p,prefix+p.relative_to(base).as_posix()))
files.append((start,'START-HERE.html'))
checksums=[]
for p,name in files:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    checksums.append(h.hexdigest()+'  '+name)
checksum=extra/'SHA256SUMS-COMPLETE.txt';checksum.write_text('\n'.join(checksums)+'\n')
files.append((checksum,checksum.name))
# The package omits itself. Point its one re-download action back to the live copy.
offline=extra/'files.html'
offline.write_text((ROOT/'site/files.html').read_text().replace('href="downloads/steven-schrembeck-complete.zip"','href="https://steven-schrembeck-archive.opzero.sh/downloads/steven-schrembeck-complete.zip"'))
files=[(offline if name=='files.html' else p,name) for p,name in files]
# Recompute the entry affected by the offline link.
checksums=[hashlib.sha256(offline.read_bytes()).hexdigest()+'  files.html' if x.endswith('  files.html') else x for x in checksums]
checksum.write_text('\n'.join(checksums)+'\n')
def write_zip(target,entries):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for source,name in entries:
            info=zipfile.ZipInfo(name,date_time=(2026,10,10,0,0,0));info.external_attr=0o100644<<16
            with source.open('rb') as f,z.open(info,'w',force_zip64=True) as dest:shutil.copyfileobj(f,dest,1024*1024)
    h=hashlib.sha256()
    with target.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    print(target.name,target.stat().st_size,h.hexdigest(),flush=True)
    return h.hexdigest()+'  '+target.name
full=OUT/'steven-schrembeck-complete.zip'
full_sum=write_zip(full,files)
(OUT/'steven-schrembeck-complete.zip.sha256').write_text(full_sum+'\n')
releases=OUT/'releases';releases.mkdir(exist_ok=True)
groups=[[]];size=0
for entry in files:
    n=entry[0].stat().st_size
    if size+n>1800*1024*1024 and groups[-1]:groups.append([]);size=0
    groups[-1].append(entry);size+=n
sums=[]
for number,group in enumerate(groups,1):
    sums.append(write_zip(releases/f'steven-schrembeck-part-{number:02d}-of-{len(groups):02d}.zip',group))
(releases/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n')
(releases/'READ-ME-FIRST.txt').write_text('Download every ZIP part and extract them into the SAME folder. Each is a normal ZIP file, not a split stream. Then open START-HERE.html. Keep SHA256SUMS-COMPLETE.txt with the extracted files. The complete collection is also in the repository through Git LFS.\n')
