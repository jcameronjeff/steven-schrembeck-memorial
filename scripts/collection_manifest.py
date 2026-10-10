"""Record exact preserved bytes, independently of older retrieval inventories."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
files=[]
for p in sorted((ROOT/'collection').rglob('*')):
    if not p.is_file() or p.name=='.DS_Store': continue
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    files.append({'path':p.relative_to(ROOT/'collection').as_posix(),'size':p.stat().st_size,'sha256':h.hexdigest(),'lfs':p.suffix in {'.mp3','.mp4','.mkv','.webm'}})
(ROOT/'collection-manifest.json').write_text(json.dumps({'date':'2026-10-10','files':files},ensure_ascii=False,indent=2)+'\n')
print(len(files),'files;',sum(x['size'] for x in files),'bytes;',sum(x['lfs'] for x in files),'LFS objects')
