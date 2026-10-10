import pathlib,json,html,urllib.parse,shutil,datetime,collections,hashlib,re
BASE=pathlib.Path(__file__).resolve().parent.parent;OUT=BASE/'outputs';D=json.loads((OUT/'job-ledger.json').read_text());ROOT=pathlib.Path(D['archive_root']);T=ROOT/'transcripts';P=T/'provenance';P.mkdir(exist_ok=True)
for source,name in [(BASE/'work/original-metadata','pre-transcription'),(BASE/'work/pre-integration-metadata','with-cox-additions')]:
 dest=P/name;dest.mkdir(exist_ok=True)
 for p in source.iterdir():
  if p.is_file() and not (dest/p.name).exists():shutil.copy2(p,dest/p.name)
for name in ['pilot-plan.json','pilot-crosschecks.json','PILOT-REVIEW.md','preflight-verification.json','original-checksum-verification.json']:
 shutil.copy2(OUT/name,T/name)
shutil.copy2(BASE/'work/video-timing.json',T/'video-timing.json')
shutil.copy2(BASE/'work/decoded-audio-validation.json',T/'decoded-audio-validation.json')
# Add links to the current archive index, preserving all intervening additions.
index=ROOT/'index.html';text=index.read_text();text=re.sub(r'<!-- transcription-nav -->.*?<!-- /transcription-nav -->','',text,flags=re.S)
nav='<!-- transcription-nav --><section><h2>Transcripts and offline search</h2><p><a href="transcripts/index.html">Search all transcripts offline</a> · <a href="transcripts/REVIEW.html">Review flagged passages</a> · <a href="transcripts/REPORT.md">Transcription report</a></p></section><!-- /transcription-nav -->\n'
pos=text.find('<h2>');text=text[:pos]+nav+text[pos:]
text=re.sub(r'<!-- transcript-links -->.*?<!-- /transcript-links -->','',text)
lines=text.splitlines(keepends=True)
for i,line in enumerate(lines):
 if '<li>' not in line:continue
 decoded=urllib.parse.unquote(html.unescape(line))
 for j in D['jobs']:
  if j['status']=='completed' and j['source_path'] in decoded:
   links=' · '.join(f'<a href="{j["transcript_files"][ext]}">{label}</a>' for ext,label in [('html','Transcript'),('srt','SRT'),('vtt','VTT'),('json','JSON')]);lines[i]=line.replace('</li>','<!-- transcript-links --><small> · '+links+'</small><!-- /transcript-links --></li>');break
index.write_text(''.join(lines))
flags=[];by_type=collections.Counter();summaries=[]
for j in D['jobs']:
 if j['status']!='completed':continue
 r=json.loads((ROOT/j['transcript_files']['review']).read_text());c=collections.Counter(x['kind'] for x in r['automated_flags']);by_type.update(c)
 if r['automated_flags']:
  summaries.append({'title':j['title'],'source_path':j['source_path'],'counts':dict(c),'flags':r['automated_flags']})
  for f in r['automated_flags']:flags.append({'source_path':j['source_path'],**f})
(T/'review-queue.json').write_text(json.dumps({'note':'Candidates for review, not confirmed errors. Machine text is uncorrected.','counts':dict(by_type),'recordings':summaries},ensure_ascii=False,indent=2)+'\n')
parts=[]
for j in D['jobs']:
 if j['status']!='completed':continue
 r=json.loads((ROOT/j['transcript_files']['review']).read_text())
 if not r['automated_flags']:continue
 parts.append('<h2>'+html.escape(j['title'])+'</h2><ul>')
 for f in r['automated_flags']:
  start=f.get('start',0);href='machine/'+j['source_sha256']+'.html#t='+str(start);detail=f.get('text',f.get('note','Check source audio; may be silence/music.'))
  parts.append(f'<li><a href="{href}">{int(start//60):02}:{int(start%60):02}</a> {html.escape(f["kind"])}: {html.escape(str(detail))}</li>')
 parts.append('</ul>')
(T/'REVIEW.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Transcript review queue</title><style>body{font:18px/1.6 system-ui;max-width:950px;margin:40px auto;padding:0 24px;background:#f7f4ee;color:#24211d}a{color:#824d31}li{margin:10px 0}</style><a href="index.html">Transcript search</a><h1>Passages for review</h1><p>These are automated candidates, not confirmed errors. Long gaps may be music or silence. Low model confidence can miss errors and can flag correct words. All machine transcripts remain uncorrected.</p><p>Known pilot issue: Reality 101 spells Steven’s name “Stephen Schrimbeck.” Mortal Steel Episode 1 places its opening word across music, approximately 40 seconds too early. See <a href="PILOT-REVIEW.md">pilot review</a>. Names, dramatic voices and speaker identities need human review.</p>'+''.join(parts)+'</html>')
notes='''\n\n<!-- transcription-notes -->
## Machine transcription — October 10, 2026

The original 63 audio recordings and 22 Seeking Minima videos have Scribe v2 machine transcripts in **transcripts/machine/**. Start with **transcripts/index.html** for offline full-text search, readable transcripts, SRT/VTT subtitles and untouched API JSON. The two subsequently added Cox videos reuse their supplied transcripts; neither was sent for paid transcription. All 87 current media files have transcript associations in transcripts/associations.json.

Machine transcripts are uncorrected. New speaker labels are neutral and local to each recording. Words, names, speaker separation and timing can contain errors; review candidates and pilot findings are available in transcripts/REVIEW.html and transcripts/PILOT-REVIEW.md. Independent local recognition checks are not a human listening review. No corrected editions have been created. Supplied Cox captions retain their existing source attribution and provenance.

The 22 video audio tracks were extracted separately in this transcription chat's work/video-audio directory without cuts, resampling or channel mixing. No recording required splitting. All checked video audio offsets are zero relative to original playback; timing metadata is retained in transcripts/video-timing.json. Original media bytes are unchanged.

transcripts/provenance/ preserves metadata and checksums from before transcription and after the concurrent Cox additions. The original retrieval inventory and manifest remain intact; transcripts/transcription-manifest.jsonl adds transcription provenance, and SHA256SUMS.txt is refreshed to cover retained archive files. See transcripts/REPORT.md for coverage, costs and verification. Nothing has been published or submitted to the Internet Archive.
<!-- /transcription-notes -->
'''
p=ROOT/'README.md';s=re.sub(r'\n*<!-- transcription-notes -->.*?<!-- /transcription-notes -->\n*','',p.read_text(),flags=re.S);p.write_text(s+notes)
(T/'transcription-manifest.jsonl').write_text(''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in D['jobs']+D.get('reused_existing_transcripts',[])))
print('Integrated',sum(j['status']=='completed' for j in D['jobs']),'new transcripts;',len(flags),'review candidates')
