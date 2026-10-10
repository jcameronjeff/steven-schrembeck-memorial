import pathlib,json,hashlib,subprocess,datetime,collections,concurrent.futures,os
ROOT=pathlib.Path('/Users/opz/Documents/Codex/2026-10-10/i/outputs/steven-schrembeck-archive')
BASE=pathlib.Path('/Users/opz/Documents/Codex/2026-10-10/transcribe-the-steven-schrembeck-preservation-archive')
OUT=BASE/'outputs'; WORK=BASE/'work'; EX=WORK/'video-audio'; EX.mkdir(exist_ok=True)
if (OUT/'job-ledger.json').exists():
 previous=json.loads((OUT/'job-ledger.json').read_text())
 if previous.get('submitted_requests',0) or any(j.get('attempts') for j in previous.get('jobs',[])):
  raise SystemExit('Refusing to overwrite a ledger with submission history.')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,data):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');os.replace(t,p)
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout
inv=json.loads((ROOT/'inventory.json').read_text()); av=json.loads((ROOT/'audio-validation.json').read_text()); vv=json.loads((ROOT/'video-validation.json').read_text())
media=[x for x in inv if x['kind'] in ('audio','video') and x['status']=='saved']; validations={x['path']:x for x in av+vv}
assert len(av)==63 and len(vv)==22 and len(media)==85
assert {x['path'] for x in media}==set(validations)
existing=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and (p.suffix.lower() in ('.srt','.vtt') or 'transcript' in p.name.lower())]
checksum_rows=[]
for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
 h,rel=line.split('  ',1); checksum_rows.append((h,rel))
def check(row):
 h,rel=row;p=ROOT/rel;actual=sha(p) if p.is_file() else None
 return dict(path=rel,expected=h,actual=actual,valid=h==actual)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(check,checksum_rows))
save(OUT/'original-checksum-verification.json',checks)
assert all(x['valid'] for x in checks),'Original checksum mismatches'
print('Original checksums verified:',len(checks),flush=True)
hashes={x['path']:x['actual'] for x in checks}
def prepare(x):
 rel=x['path']; src=ROOT/rel; checksum=hashes.get(rel) or sha(src)
 assert checksum==x['sha256'],rel
 probe=json.loads(run(['/opt/homebrew/bin/ffprobe','-v','error','-show_format','-show_streams','-of','json',str(src)]))
 a=next(s for s in probe['streams'] if s['codec_type']=='audio')
 payload=run(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(src),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-']).strip().split('=')[-1]
 row=dict(source_path=rel,source_sha256=checksum,source_bytes=src.stat().st_size,title=x.get('title',''),kind=x['kind'],duration_seconds=float(probe['format']['duration']),audio_codec=a['codec_name'],sample_rate=a.get('sample_rate'),channels=a.get('channels'),encoded_audio_payload_sha256=payload,source_format_start_seconds=float(probe['format'].get('start_time',0)),source_audio_stream_start_seconds=float(a.get('start_time',0)),model='scribe_v2',status='blocked_missing_api_key',transcription_date=None,attempts=[],transcript_files={},estimated_base_usd=float(probe['format']['duration'])/3600*.22)
 if x['kind']=='video':
  # Decode complete source audio to lossless FLAC without cuts, resampling or channel mixing.
  target=EX/(checksum+'.flac');tmp=EX/(checksum+'.partial.flac')
  if not target.exists():
   run(['/opt/homebrew/bin/ffmpeg','-v','error','-nostdin','-i',str(src),'-map','0:a:0','-vn','-c:a','flac','-y',str(tmp)]);os.replace(tmp,target)
  ep=json.loads(run(['/opt/homebrew/bin/ffprobe','-v','error','-show_format','-show_streams','-of','json',str(target)]))
  row.update(prepared_audio_path=str(target),prepared_audio_sha256=sha(target),prepared_audio_duration_seconds=float(ep['format']['duration']),offset_review_required=True)
  # Explicitly preserve source timing metadata; pilot must verify playback offset before exports.
 else:row['prepared_audio_path']=str(src)
 print('Prepared',rel,flush=True);return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(prepare,media))
groups=collections.defaultdict(list)
for x in rows:groups[x['source_sha256']].append(x['source_path'])
payload_groups=collections.defaultdict(list)
for x in rows:payload_groups[(x['encoded_audio_payload_sha256'],x['sample_rate'],x['channels'])].append(x['source_path'])
for x in rows:x['job_key']=x['source_sha256']+'-scribe_v2-word-diarized-v1'
ledger=dict(version=1,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archive_root=str(ROOT),budget_usd=15,submitted_requests=0,actual_transcription_cost_usd=0,account_access='Connected creative catalog accessible; only eleven_scribe_v1 advertised. ELEVENLABS_API_KEY absent. Scribe v2 account limits and balance unverified.',jobs=rows)
save(OUT/'job-ledger.json',ledger)
summary=dict(verified_at_utc=ledger['created_utc'],original_checksum_count=len(checks),original_checksum_failures=[],saved_audio=len(av),saved_video=len(vv),media_count=len(rows),total_hours=sum(x['duration_seconds'] for x in rows)/3600,total_estimated_base_usd=sum(x['estimated_base_usd'] for x in rows),rate_usd_per_hour=.22,pricing_source='https://elevenlabs.io/pricing/api',price_excludes_tax=True,exact_file_duplicate_groups=[g for g in groups.values() if len(g)>1],exact_encoded_audio_duplicate_groups=[g for g in payload_groups.values() if len(g)>1],existing_transcript_files=existing,video_audio_extractions=sum(x['kind']=='video' for x in rows),prior_collection_failures=[x for x in inv if x['kind']=='audio' and x['status']=='failed'],transcriptions_completed=0,submitted_requests=0,source_archive_unchanged=True)
save(OUT/'preflight-verification.json',summary)
print(json.dumps(summary,indent=2),flush=True)
