import pathlib,json,re,hashlib,html.parser,urllib.parse,collections,math
BASE=pathlib.Path(__file__).resolve().parent.parent;OUT=BASE/'outputs';d=json.loads((OUT/'job-ledger.json').read_text());ROOT=pathlib.Path(d['archive_root']);d=json.loads((ROOT/'transcripts/associations.json').read_text());fail=[];checks=[]
def parse_time(t):
 h,m,s=re.split(':',t);return int(h)*3600+int(m)*60+float(s.replace(',','.'))
class Links(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ('href','src') and v:self.links.append(v)
for j in d['jobs']:
 if j['status']!='completed':continue
 row={'source_path':j['source_path'],'files_checked':0};stem=j['source_sha256']
 for ext in ['json','txt','srt','vtt','html','review']:
  rel=j['transcript_files'].get(ext);p=ROOT/rel if rel else None
  if not p or not p.is_file():fail.append({'source':j['source_path'],'issue':'Missing '+ext});continue
  row['files_checked']+=1
 raw=(ROOT/j['transcript_files']['json']).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=j['raw_response_sha256']:fail.append({'source':j['source_path'],'issue':'Raw response checksum changed'})
 r=json.loads(raw);spoken=[w for w in r['words'] if w['type']=='word'];row['spoken_words']=len(spoken);row['language']=r.get('language_code')
 for ext in ['srt','vtt']:
  text=(ROOT/j['transcript_files'][ext]).read_text()
  if ext=='vtt' and not text.startswith('WEBVTT\n'):fail.append({'source':j['source_path'],'issue':'VTT header'})
  if ext=='vtt':text=text.split('\n',2)[2]
  blocks=[x for x in re.split(r'\n\s*\n',text.strip()) if x.strip()];last=-1;overlaps=0;lastend=-1
  for i,b in enumerate(blocks,1):
   lines=b.splitlines();valid=len(lines)>=3 and lines[0]==str(i) and re.fullmatch(r'\d{2,}:\d{2}:\d{2}[,.]\d{3} --> \d{2,}:\d{2}:\d{2}[,.]\d{3}',lines[1])
   if not valid:fail.append({'source':j['source_path'],'issue':ext+' invalid cue '+str(i)});continue
   a,z=map(parse_time,lines[1].split(' --> '))
   if not (0<=a<z<=j['duration_seconds']+.501 and a>=last):fail.append({'source':j['source_path'],'issue':ext+' timestamp '+str(i)})
   if a<lastend:overlaps+=1
   last=a;lastend=z
  row[ext+'_cues']=len(blocks);row[ext+'_overlapping_cues']=overlaps
 checks.append(row)
link_checks=0
for p in [p for p in (ROOT/'transcripts').rglob('*.html') if 'provenance' not in p.relative_to(ROOT/'transcripts').parts]+[ROOT/'index.html']+[ROOT/x['transcript_files']['html'] for x in d.get('reused_existing_transcripts',[])]:
 parser=Links();parser.feed(p.read_text())
 for link in parser.links:
  u=urllib.parse.urlsplit(link)
  if u.scheme or u.netloc or not u.path:continue
  dest=(p.parent/urllib.parse.unquote(u.path)).resolve();link_checks+=1
  if not dest.exists():fail.append({'source':str(p.relative_to(ROOT)),'issue':'Broken link '+link})
search=(ROOT/'transcripts/search-data.js').read_text();search_records=json.loads(search.split('=',1)[1].strip().removesuffix(';'))
for r in search_records:
 link_checks+=1
 if not (ROOT/'transcripts'/urllib.parse.unquote(urllib.parse.urlsplit(r['href']).path)).resolve().exists():fail.append({'source':'transcripts/search-data.js','issue':'Broken search result '+r['href']})
if (ROOT/'index.html').read_text().count('<!-- transcript-links -->')!=85:fail.append({'source':'index.html','issue':'Expected 85 direct transcript link groups'})
# Compare preserved originals against the original manifest, allowing only explicitly updated collection notes/index.
baseline=json.loads((OUT/'original-checksum-verification.json').read_text());changed=[]
for row in baseline:
 p=ROOT/row['path'];h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 if h.hexdigest()!=row['expected']:changed.append(row['path'])
for p in changed:
 if p not in ['README.md','index.html','inventory.json','inventory.csv','video-validation.json','manifest.jsonl']:fail.append({'source':p,'issue':'Unexpected change to original'})
# Verify original inventory and validation records remain present and unchanged.
for name in ['inventory.json','video-validation.json']:
 old=json.loads((BASE/'work/original-metadata'/name).read_text());new={x['path']:x for x in json.loads((ROOT/name).read_text())}
 for x in old:
  if new.get(x['path'])!=x:fail.append({'source':name,'issue':'Original record changed: '+x['path']})
if not (ROOT/'manifest.jsonl').read_bytes().startswith((BASE/'work/original-metadata/manifest.jsonl').read_bytes()):fail.append({'source':'manifest.jsonl','issue':'Original retrieval history no longer preserved as prefix'})
assoc=json.loads((ROOT/'transcripts/associations.json').read_text());media={x['path'] for x in json.loads((ROOT/'inventory.json').read_text()) if x['kind'] in ['audio','video'] and x['status']=='saved'}
for imported in assoc.get('reused_existing_transcripts',[]):
 p=ROOT/imported['source_path'];h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 if h.hexdigest()!=imported['source_sha256']:fail.append({'source':imported['source_path'],'issue':'Supplied video checksum mismatch'})
 for rel in imported['transcript_files'].values():
  if not (ROOT/rel).is_file():fail.append({'source':imported['source_path'],'issue':'Missing supplied transcript '+rel})
covered={j['source_path'] for j in assoc['jobs'] if j['status']=='completed'}|{j['source_path'] for j in assoc.get('reused_existing_transcripts',[])}
report={'completed':len(checks),'expected_media':len(d['jobs']),'current_inventory_media_count':len(media),'associated_media_count':len(covered),'uncovered_media':sorted(media-covered),'status_counts':dict(collections.Counter(j['status'] for j in d['jobs'])),'checks':checks,'local_link_scope':'Active archive and transcript pages; byte-preserved historical HTML snapshots are excluded because their relative base is the original archive root.','local_links_checked':link_checks,'changed_original_files':changed,'failures':fail,'note':'Overlapping cues are retained when source speaker turns overlap. Unusually long word timestamps are flagged for review rather than silently retimed.'}
(OUT/'verification-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2));assert not fail
