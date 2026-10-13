from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
import json
import argparse
ROOT=Path(__file__).resolve().parents[1]
args=argparse.ArgumentParser()
args.add_argument('--site',type=Path,default=ROOT/'site')
site=args.parse_args().site.resolve()
(ROOT/'qa').mkdir(exist_ok=True)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set();self.h1=0
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.add(a['id'])
  if t=='h1':self.h1+=1
  for k in ['href','src']:
   if a.get(k):self.links.append((t,a[k]))
errors=[];total=0;parsers={}
for p in site.rglob('*.html'):
 if 'collection-files' in p.parts:continue
 parser=Links();parser.feed(p.read_text());parsers[p.resolve()]=parser
 if parser.h1!=1:errors.append(f'{p.name}: {parser.h1} h1 headings')
for p,parser in parsers.items():
 for tag,url in parser.links:
  u=urlsplit(url)
  if u.scheme or u.netloc:continue
  path=(p.parent/unquote(u.path)).resolve() if u.path else p
  if path.name=='steven-schrembeck-complete.zip':continue
  if not path.exists():errors.append(f'{p.name}: missing {url}')
  elif u.fragment and path in parsers and unquote(u.fragment) not in parsers[path].ids:errors.append(f'{p.name}: missing anchor {url}')
  total+=1
summary={'pages':len(parsers),'links_checked':total,'errors':errors}
(ROOT/'qa/link-validation.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));raise SystemExit(bool(errors))
