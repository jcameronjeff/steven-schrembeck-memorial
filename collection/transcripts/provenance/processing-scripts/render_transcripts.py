import pathlib,json,html,datetime,re,math,collections,textwrap,hashlib,urllib.parse,shutil,sys
BASE=pathlib.Path(__file__).resolve().parent.parent;OUT=BASE/'outputs';ROOT=pathlib.Path('/Users/opz/Documents/Codex/2026-10-10/i/outputs/steven-schrembeck-archive');T=ROOT/'transcripts';M=T/'machine'
def ts(n,comma=False):
 ms=max(0,round(n*1000));h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02}{"," if comma else "."}{ms:03}'
def label(s):
 return 'Speaker '+str(int(s.split('_')[-1])+1) if s and re.fullmatch(r'speaker_\d+',s) else 'Unassigned speaker'
def cue_words(words):
 cues=[];cur=[]
 for w in words:
  if w.get('type')=='spacing':continue
  if cur and (w.get('speaker_id')!=cur[-1].get('speaker_id') or w['end']-cur[0]['start']>6 or sum(len(x['text'])+1 for x in cur)+len(w['text'])>84 or w['start']-cur[-1]['end']>1.5):
   cues.append(cur);cur=[]
  cur.append(w)
 if cur:cues.append(cur)
 return cues

def render(j):
 stem=j['source_sha256'];raw=M/(stem+'.json');r=json.loads(raw.read_text());offset=j.get('original_media_offset_seconds',0);words=[];flags=[]
 for name in ['pilot-crosschecks.json','supplemental-crosschecks.json']:
  cross=OUT/name
  if cross.exists():
   for check in json.loads(cross.read_text()):
    if check['source_path']==j['source_path'] and check['normalized_sequence_agreement']<.9:flags.append({'kind':'cross_recognizer_disagreement','start':check['start_seconds'],'end':check['end_seconds'],'note':'Scribe and independent local recognition disagree. Neither is ground truth; compare with source audio.','evidence':name})
 for i,w in enumerate(r['words']):
  if w.get('start') is None or w.get('end') is None:
   raise ValueError('Missing raw timestamp in '+j['source_path']+' word '+str(i))
  w=dict(w);w['start']+=offset;w['end']+=offset
  if not all(math.isfinite(w[x]) for x in ['start','end']) or w['start']<0 or w['end']<w['start'] or w['end']>j['duration_seconds']+.5:
   raise ValueError('Invalid raw timestamp in '+j['source_path']+' word '+str(i))
  if w.get('type')=='word' and w['end']-w['start']>3:
   flags.append({'kind':'word_duration_over_3s','word_index':i,'text':w['text'],'start':w['start'],'end':w['end'],'note':'Suspicious word alignment; raw timestamp preserved.'})
  if w.get('logprob') is not None and w['logprob'] < -1:
   flags.append({'kind':'low_word_logprob','word_index':i,'start':w['start'],'end':w['end'],'text':w['text'],'logprob':w['logprob']})
  if w.get('type')=='word' and 'schrimbeck' in w['text'].lower():flags.append({'kind':'catalog_name_spelling_review','word_index':i,'start':w['start'],'end':w['end'],'text':w['text'],'note':'Catalog spells the author Steven Schrembeck; machine text retained.'})
  words.append(w)
 timed=[w for w in words if w.get('type')!='spacing'];speech=[w for w in timed if w.get('type')=='word'];speakers=sorted(set(w.get('speaker_id') for w in speech if w.get('speaker_id')))
 for a,b in zip(speech,speech[1:]):
  if b['start']-a['end']>20:flags.append({'kind':'speech_gap_over_20s','start':a['end'],'end':b['start'],'note':'May be music, silence or an omission; review audio.'})
 if speech:
  if speech[0]['start']>20:flags.append({'kind':'leading_no_speech','start':0,'end':speech[0]['start']})
  if j['duration_seconds']-speech[-1]['end']>20:flags.append({'kind':'trailing_no_speech','start':speech[-1]['end'],'end':j['duration_seconds']})
 else:flags.append({'kind':'no_words'})
 # Stable timestamp ordering accommodates simultaneous speakers; untouched JSON retains API order.
 timed=sorted(timed,key=lambda w:(w['start'],w['end']));cues=cue_words(timed);rendered=[]
 for c in cues:
  start=c[0]['start'];end=max(w['end'] for w in c);text=' '.join(w['text'] for w in c);end=max(end,start+.001)
  rendered.append({'start':start,'end':end,'speaker':label(c[0].get('speaker_id')),'text':text})
 j['transcript_files'].update({ext:f'transcripts/machine/{stem}.{ext}' for ext in ['txt','srt','vtt','html']});j['transcript_files']['review']=f'transcripts/machine/{stem}.review.json'
 head=f'{j["title"]}\nSource: {j["source_path"]}\nSHA-256: {stem}\nModel: scribe_v2 | Transcribed: {j["transcription_date"]}\nMachine transcript — uncorrected. Speaker labels are local to this recording and do not identify people.\n\n'
 # Readable paragraphs preserve API token order and spelling; only paragraph boundaries are generated.
 paragraphs=[];group=[]
 for w in words:
  if w.get('type')=='spacing':
   if group:group.append(w)
   continue
  real=[x for x in group if x.get('type')!='spacing']
  if real and (w.get('speaker_id')!=real[-1].get('speaker_id') or w['end']-real[0]['start']>35):paragraphs.append(group);group=[]
  group.append(w)
 if group:paragraphs.append(group)
 lines=[]
 for p in paragraphs:
  real=[x for x in p if x.get('type')!='spacing']
  if not real:continue
  text=''.join(w['text'] for w in p).strip();lines.append(f'[{ts(real[0]["start"])}] {label(real[0].get("speaker_id"))}: {text}')
 (M/(stem+'.txt')).write_text(head+'\n\n'.join(lines)+'\n')
 srt=[];vtt=['WEBVTT','']
 for i,c in enumerate(rendered,1):
  text=c['speaker']+': '+c['text'];wrapped='\n'.join(textwrap.wrap(text,width=48,break_long_words=False,break_on_hyphens=False))
  srt.append(f'{i}\n{ts(c["start"],True)} --> {ts(c["end"],True)}\n{wrapped}\n');vtt.append(f'{i}\n{ts(c["start"])} --> {ts(c["end"])}\n{html.escape(wrapped,quote=False)}\n')
 (M/(stem+'.srt')).write_text('\n'.join(srt));(M/(stem+'.vtt')).write_text('\n'.join(vtt))
 review={'source_path':j['source_path'],'automated_flags':flags,'flags_are_review_candidates_not_confirmed_errors':True,'raw_word_count':len(r['words']),'spoken_word_count':len(speech),'speaker_ids':speakers,'subtitle_cue_count':len(rendered),'first_speech_seconds':speech[0]['start'] if speech else None,'last_speech_seconds':speech[-1]['end'] if speech else None,'human_correction_status':'uncorrected','source_offset_seconds':offset}
 (M/(stem+'.review.json')).write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');j['review_flag_count']=len(flags)
 source='../../'+urllib.parse.quote(j['source_path']);tag='video' if j['kind']=='video' else 'audio';player=f'<{tag} controls preload="metadata" src="{source}"></{tag}>'
 body=''.join(f'<p><a href="#" data-time="{c["start"]}">{ts(c["start"])}</a> <b>{html.escape(c["speaker"])}</b> {html.escape(c["text"])}</p>' for c in rendered)
 caption_json=json.dumps(rendered,ensure_ascii=False).replace('<','\\u003c')
 (M/(stem+'.html')).write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(j["title"])}</title><style>body{{font:18px/1.6 system-ui;max-width:900px;margin:32px auto;padding:0 20px;background:#f7f4ee;color:#24211d}}audio,video{{width:100%;max-height:60vh}}a{{color:#824d31}}small{{overflow-wrap:anywhere}}</style><a href="../index.html">All transcripts and search</a><h1>{html.escape(j["title"])}</h1><p>Uncorrected Scribe v2 machine transcript. Neutral speaker labels are specific to this recording. Review flags: {len(flags)}.</p><p><a href="{stem}.txt">TXT</a> · <a href="{stem}.srt">SRT</a> · <a href="{stem}.vtt">VTT</a> · <a href="{stem}.json">Untouched JSON</a> · <a href="{stem}.review.json">Review flags</a></p>{player}<p><small>Source: {html.escape(j["source_path"])}<br>SHA-256: {stem}</small></p>{body}<script>const player=document.querySelector("audio,video");const cueData={caption_json};if(typeof VTTCue!=="undefined"){{const captions=player.addTextTrack("subtitles","Machine transcript","en");for(const c of cueData){{const text=(c.speaker+": "+c.text).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");captions.addCue(new VTTCue(c.start,c.end,text));}}captions.mode="hidden";}}document.querySelectorAll("[data-time]").forEach(a=>a.onclick=e=>{{e.preventDefault();let p=document.querySelector("audio,video");p.currentTime=Number(a.dataset.time);p.play();}});const initial=Number(new URLSearchParams(location.hash.slice(1)).get("t"));if(initial>0){{if(player.readyState>=1)player.currentTime=initial;else player.addEventListener("loadedmetadata",()=>{{player.currentTime=initial;}},{{once:true}});}}</script></html>')
 return {'title':j['title'],'source':j['source_path'],'href':f'machine/{stem}.html','text':r['text'],'segments':rendered,'flags':len(flags),'speakers':len(speakers),'duration_seconds':j['duration_seconds']}

def main():
 d=json.loads((OUT/'job-ledger.json').read_text());timing={x['source_path']:x for x in json.loads((BASE/'work/video-timing.json').read_text())}
 decoded_path=BASE/'work/decoded-audio-validation.json'
 decoded={x['source_path']:x for x in json.loads(decoded_path.read_text())} if decoded_path.exists() else {}
 records=[]
 for j in d['jobs']:
  if j['source_path'] in decoded and decoded[j['source_path']]['readable']:
   j.setdefault('container_duration_seconds',j['duration_seconds']);j['decoded_audio_duration_seconds']=decoded[j['source_path']]['decoded_audio_duration_seconds']
   if j['kind']=='audio':j['duration_seconds']=j['decoded_audio_duration_seconds']
  if j['source_path'] in timing:j.update(timing[j['source_path']]);j['offset_review_required']=False
  if j['status']=='completed':records.append(render(j))
 existing=[]
 for cp in sorted((ROOT/'cox-workplace/presentations').glob('*/cues.json')):
  folder=cp.parent;meta=json.loads((folder/'metadata.json').read_text());cues=json.loads(cp.read_text());videos=list(folder.glob('*.mp4'))
  if not videos:continue
  video=videos[0];rel=str(video.relative_to(ROOT));inv=next(x for x in json.loads((ROOT/'inventory.json').read_text()) if x['path']==rel);validation=next(x for x in json.loads((ROOT/'video-validation.json').read_text()) if x['path']==rel);duration=float(validation['probe']['format']['duration'])
  existing.append({'source_path':rel,'source_sha256':inv['sha256'],'status':'existing_transcript_reused','model':meta.get('transcription_model'),'transcription_date':meta.get('transcription_date'),'paid_submission':False,'transcript_files':{'html':str((folder/'READ.html').relative_to(ROOT)),'txt':str((folder/'transcript.txt').relative_to(ROOT)),'srt':str((folder/'transcript.srt').relative_to(ROOT)),'vtt':str(next(folder.glob('*.vtt')).relative_to(ROOT)),'json':str(cp.relative_to(ROOT))},'note':'User-supplied captions with retained speaker attribution; source model/date unknown. JSON contains preserved cues, not an ElevenLabs response.'})
  records.append({'title':meta['title']+' [supplied captions]','source':rel,'href':'../'+urllib.parse.quote(str((folder/'READ.html').relative_to(ROOT))),'text':' '.join(c['text'] for c in cues),'segments':[{'start':c['start_ms']/1000,'end':c['end_ms']/1000,'text':c['text'],'speaker':c['speaker']} for c in cues],'flags':0,'speakers':len({c['speaker'] for c in cues}),'duration_seconds':duration,'provenance':'Supplied captions; not new Scribe output'})
 d['reused_existing_transcripts']=existing
 (T/'associations.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 if '--snapshot' not in sys.argv:(OUT/'job-ledger.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 (T/'search-data.js').write_text('const TRANSCRIPTS = '+json.dumps(records,ensure_ascii=False).replace('<','\\u003c')+';\n')
 (T/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Steven Schrembeck — transcript search</title><style>body{max-width:1000px;margin:40px auto;padding:0 24px;background:#f7f4ee;color:#24211d;font:18px/1.6 system-ui}a{color:#824d31}input{font:inherit;padding:12px;width:90%;border:1px solid #888;border-radius:6px}article{border-top:1px solid #c5bbaa;padding:16px 0}small{color:#655c50}mark{background:#ffdf8a}h2{font-size:1.15em}#status{min-height:2em}</style><a href="../index.html">Archive home</a><h1>Transcripts and offline search</h1><p>Uncorrected ElevenLabs Scribe v2 transcripts, plus two existing supplied workplace transcripts. New speaker labels do not establish identity; supplied captions retain their original attribution. Search works offline without a server. Select a transcript to play the source and jump to timestamps.</p><label for="q">Search all transcript text</label><br><input id="q" type="search" placeholder="Enter words or a phrase"><p id="status" aria-live="polite"></p><div id="results"></div><script src="search-data.js"></script><script>
const q=document.getElementById('q'),results=document.getElementById('results'),status=document.getElementById('status');
function show(){const term=q.value.trim().toLocaleLowerCase();results.replaceChildren();let count=0;for(const r of TRANSCRIPTS){if(term&&!r.text.toLocaleLowerCase().includes(term)&&!r.title.toLocaleLowerCase().includes(term))continue;count++;const a=document.createElement('article'),h=document.createElement('h2'),link=document.createElement('a');link.href=r.href;link.textContent=r.title;h.append(link);a.append(h);const meta=document.createElement('small');meta.textContent=r.source+' · '+Math.round(r.duration_seconds/60)+' min · '+r.speakers+' speaker labels · '+r.flags+' review flags';a.append(meta);if(term){let matches=r.segments.filter(s=>s.text.toLocaleLowerCase().includes(term)).slice(0,5);if(!matches.length){const p=document.createElement('p');p.textContent='Match in title or across subtitle boundaries; open transcript and use Find.';a.append(p);}for(const s of matches){const p=document.createElement('p');p.textContent='['+Math.floor(s.start/60)+':'+String(Math.floor(s.start%60)).padStart(2,'0')+'] '+s.text;a.append(p);}}results.append(a);}status.textContent=count+' of '+TRANSCRIPTS.length+' recordings'+(term?' match':' available');}q.addEventListener('input',show);show();</script></html>''')
 print('Rendered',len(records),'recordings; flags',sum(r['flags'] for r in records))
if __name__=='__main__':main()
