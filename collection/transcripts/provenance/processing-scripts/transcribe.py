import pathlib,json,os,datetime,hashlib,threading,concurrent.futures,http.client,ssl,uuid,fcntl,sys,math
BASE=pathlib.Path(__file__).resolve().parent.parent; OUT=BASE/'outputs'; WORK=BASE/'work'; LEDGER=OUT/'job-ledger.json'
ROOT=pathlib.Path('/Users/opz/Documents/Codex/2026-10-10/i/outputs/steven-schrembeck-archive'); TRANS=ROOT/'transcripts'; RAW=TRANS/'machine'; RAW.mkdir(parents=True,exist_ok=True)
lockfile=open(WORK/'transcription.lock','w');fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
lock=threading.Lock();stop=threading.Event();d=json.loads(LEDGER.read_text());
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():
 p=LEDGER.with_suffix('.tmp');p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');os.replace(p,LEDGER)
key=''
for line in (WORK/'.env').read_text().splitlines():
 if line.strip().startswith('ELEVENLABS_API_KEY='):key=line.split('=',1)[1].strip().strip('\"\x27')
assert key,'Missing key'
params={'model_id':'scribe_v2','timestamps_granularity':'word','diarize':'true','tag_audio_events':'true','no_verbatim':'false'}
d.pop('actual_transcription_cost_usd',None);d['request_parameters']=params;d['account_access']='Verified active Creator subscription; overage disabled';d['maximum_parallel_requests']=2;d['account_speech_to_text_concurrency_limit']=20;d['budget_reservation_rate_usd_per_hour']=.30

def submit(j):
 with lock:
  if j['status']=='completed' or stop.is_set():return
  if j.get('attempts'):print('SKIP existing attempt',j['source_path'],flush=True);return
  src=pathlib.Path(j['prepared_audio_path']); expected=j.get('prepared_audio_sha256',j['source_sha256'])
  h=hashlib.sha256()
  with src.open('rb') as f:
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  assert h.hexdigest()==expected,'Input checksum changed'
  reservation=math.ceil(j['duration_seconds']/60)*.30/60
  reserved=sum(a.get('reserved_usd',0) for x in d['jobs'] for a in x.get('attempts',[]))
  if reserved+reservation>15:raise RuntimeError('Budget cap would be exceeded')
  attempt={'local_attempt_id':str(uuid.uuid4()),'started_utc':now(),'reserved_usd':reservation,'status':'submitting','request_parameters':params,'offset_seconds':0,'input_sha256':expected}
  j['attempts'].append(attempt);j['status']='submitting';d['submitted_requests']=sum(len(x['attempts']) for x in d['jobs']);save()
 print('SUBMIT',j['source_path'],flush=True)
 boundary='----Archive'+uuid.uuid4().hex
 pre=b''
 for k,v in params.items():pre+=f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
 pre+=f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{j["source_sha256"]}{src.suffix}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode();post=f'\r\n--{boundary}--\r\n'.encode()
 stem=j['source_sha256']; response_path=RAW/(stem+'.json');headers_path=RAW/(stem+'.response-metadata.json')
 try:
  conn=http.client.HTTPSConnection('api.elevenlabs.io',timeout=1800,context=ssl.create_default_context());conn.putrequest('POST','/v1/speech-to-text');conn.putheader('xi-api-key',key);conn.putheader('Content-Type','multipart/form-data; boundary='+boundary);conn.putheader('Content-Length',str(len(pre)+src.stat().st_size+len(post)));conn.endheaders();conn.send(pre)
  with src.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):conn.send(b)
  conn.send(post);resp=conn.getresponse(); status=resp.status
  headers={k:v for k,v in resp.getheaders() if k.lower() not in ['set-cookie']}
  metadata={'http_status':status,'headers':headers,'received_utc':now(),'local_attempt_id':attempt['local_attempt_id']};headers_path.write_text(json.dumps(metadata,indent=2)+'\n')
  temp=response_path.with_suffix('.partial');
  with temp.open('wb') as f:
   while True:
    b=resp.read(1024*1024)
    if not b:break
    f.write(b)
   f.flush();os.fsync(f.fileno())
  os.replace(temp,response_path);conn.close(); body=json.loads(response_path.read_bytes())
  with lock:
   attempt.update(status='completed' if status==200 else 'http_error',http_status=status,finished_utc=now(),response_path=str(response_path),request_id=headers.get('request-id') or headers.get('Request-Id'),response_metadata_path=str(headers_path))
   if status==200:
    assert isinstance(body.get('words'),list) and 'text' in body,'Unexpected response schema'
    j.update(status='completed',usage={'character_cost':headers.get('character-cost'),'fiat_cost_before_overages':headers.get('fiat-cost-before-overages'),'currency':headers.get('fiat-currency')},transcription_date=now(),raw_response_sha256=hashlib.sha256(response_path.read_bytes()).hexdigest(),transcript_files={'json':str(response_path.relative_to(ROOT))},transcription_id=body.get('transcription_id'),response_audio_duration_seconds=body.get('audio_duration_secs'))
   else:
    j['status']='http_error';j['error']=str(body)[:1500]
    if status in (401,402,403,429):stop.set()
   save()
  print('RESULT',status,j['source_path'],'words',len(body.get('words',[])),flush=True)
 except Exception as e:
  with lock:
   attempt.update(status='unknown_outcome',error=type(e).__name__+': '+str(e),finished_utc=now());j['status']='unknown_outcome';save()
  print('UNKNOWN OUTCOME',j['source_path'],type(e).__name__,str(e),flush=True)

mode=sys.argv[1]
if mode=='pilots':
 paths={x['source_path'] for x in json.loads((OUT/'pilot-plan.json').read_text())['pilots']};jobs=[j for j in d['jobs'] if j['source_path'] in paths]
elif mode=='remaining':
 assert json.loads((OUT/'pilot-plan.json').read_text()).get('pilot_review_passed'),'Pilot review gate not passed';jobs=[j for j in d['jobs'] if j['status']!='completed']
else:raise SystemExit('Use pilots or remaining')
save()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(submit,jobs))
print('DONE', {s:sum(j['status']==s for j in d['jobs']) for s in set(j['status'] for j in d['jobs'])},flush=True)
