"""Restore and verify LFS objects from the independently uploaded R2 copy."""
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,time
ROOT=Path(__file__).resolve().parents[1]
HOST=os.environ['ARCHIVE_UPLOAD_URL'].rstrip('/')
files=json.loads((ROOT/'collection-manifest.json').read_text())['files']
def restore(item):
    path=ROOT/'collection'/item['path']
    temp=path.with_name(path.name+'.partial')
    for attempt in range(20):
        try:
            h=hashlib.sha256();size=0
            request=Request(HOST+'/'+quote(item['path'],safe='/'),headers={'User-Agent':'StevenSchrembeckArchive/1.0','Accept-Encoding':'identity'})
            with urlopen(request,timeout=180) as source, temp.open('wb') as target:
                for block in iter(lambda:source.read(1024*1024),b''):
                    h.update(block);size+=len(block);target.write(block)
            if size!=item['size'] or h.hexdigest()!=item['sha256']: raise ValueError('Checksum mismatch')
            temp.replace(path);print('Verified',item['path'],flush=True);return
        except Exception as error:
            temp.unlink(missing_ok=True)
            print('Retry',attempt+1,item['path'],type(error).__name__,str(error),flush=True)
            if isinstance(error,HTTPError) and error.code in {401,403}: raise
            if attempt==19: raise
            time.sleep(15)
with ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(restore,[i for i in files if i['lfs']]))
