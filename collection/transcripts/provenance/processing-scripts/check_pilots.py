import sys,pathlib,json,subprocess,re,difflib,os
BASE=pathlib.Path(__file__).resolve().parent.parent;sys.path.insert(0,str(BASE/'work/asr-deps'));os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
from faster_whisper import WhisperModel
import wave,numpy as np
print('Loading independent local Whisper small.en',flush=True)
model=WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=4,download_root=str(BASE/'work/asr-models'))
mode=sys.argv[1] if len(sys.argv)>1 else 'pilots'
selected={x['source_path'] for x in json.loads((BASE/'outputs/pilot-plan.json').read_text())['pilots']} if mode=='pilots' else {'interviews/nosleep-podcast-s9e09.mp3','youtube/20230408-w_mPrS11HP4-The Fix 02 - How Do You Think About Trauma？.webm','youtube/20230216-Uwj1bkST5Xk-Reverie Teaser.webm'}
output_name='pilot-crosschecks.json' if mode=='pilots' else 'supplemental-crosschecks.json'
d=json.loads((BASE/'outputs/job-ledger.json').read_text());root=pathlib.Path(d['archive_root']);checks=[];clipdir=BASE/'work/qa-clips';clipdir.mkdir(exist_ok=True)
for source in selected:
 while True:
  d=json.loads((BASE/'outputs/job-ledger.json').read_text());j=next(x for x in d['jobs'] if x['source_path']==source)
  if j['status']=='completed':break
  if mode=='pilots' or j['status'] in ['http_error','unknown_outcome']:break
  import time;time.sleep(10)
 if j['status']!='completed':continue
 raw=json.loads((root/j['transcript_files']['json']).read_text());words=[w for w in raw['words'] if w['type']=='word']
 for kind,start,length in [('beginning',0,70),('middle',j['duration_seconds']/2,35),('end',max(0,j['duration_seconds']-40),40)]:
  clip=clipdir/(j['source_sha256']+'-'+kind+'.wav');subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-ss',str(start),'-i',j['prepared_audio_path'],'-t',str(length),'-ar','16000','-ac','1',str(clip)],check=True)
  with wave.open(str(clip),'rb') as f: audio=np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).astype(np.float32)/32768
  seg,info=model.transcribe(audio,language='en',beam_size=5,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
  segments=[{'start':s.start+start,'end':s.end+start,'text':s.text,'avg_logprob':s.avg_logprob,'words':[{'start':w.start+start,'end':w.end+start,'word':w.word} for w in s.words or []]} for s in seg]
  local=' '.join(s['text'] for s in segments);scribe=' '.join(w['text'] for w in words if start<=w['start']<start+length)
  norm=lambda t:re.findall(r'[a-z0-9]+',t.lower());ratio=difflib.SequenceMatcher(None,norm(local),norm(scribe),autojunk=False).ratio()
  row={'source_path':j['source_path'],'section':kind,'start_seconds':start,'end_seconds':min(start+length,j['duration_seconds']),'scribe_text':scribe,'local_whisper_text':local,'local_whisper_segments':segments,'normalized_sequence_agreement':ratio,'not_ground_truth':True};checks.append(row)
  (BASE/'outputs'/output_name).write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(j['source_path'],kind,'agreement',round(ratio,3),flush=True)
print('Local pilot crosschecks complete',flush=True)
