#!/usr/bin/env python3
"""Build ordinary HTML from the retained collection. No dependencies or network."""
from pathlib import Path
import argparse, json, re, shutil, html
from datetime import datetime
from listening import publication_label
from explore import explore_library
from book import build_book, book_download_card
from archive_files import file_size
from contribution_pages import build_contributions, build_form

ROOT=Path(__file__).resolve().parents[1]
(ROOT/'output').mkdir(exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--archive',type=Path,default=ROOT/'collection')
args=parser.parse_args(); SRC=args.archive; OUT=ROOT/'site'
e=html.escape
for retired in ['archive.html','timeline.html','collection.html','work.html']:(OUT/retired).unlink(missing_ok=True)
for folder in ['assets','writing','downloads','recordings','transcripts']:(OUT/folder).mkdir(exist_ok=True,parents=True)
for name in ['steven-schrembeck.jpg','steven-schrembeck-family.jpg']:shutil.copy2(SRC/'memorial'/name,OUT/'assets'/name)
for folder in ['reality','collected']:shutil.copy2(SRC/folder/'cover.jpg',OUT/'assets'/f'{folder}-cover.jpg')
POSTS=json.loads((SRC/'cox-workplace/memorial/remembering-steven-schrembeck-data-2026-10-10.json').read_text())['posts']
ORIGINAL=(SRC/'memorial/READ.html').read_text()
body=ORIGINAL.split('<p>Man am I')[1].split('</article>')[0]
body='<p>Man am I'+body
body=body.replace('src="steven-schrembeck.jpg"','src="assets/steven-schrembeck.jpg"')
body=body.replace('src="steven-schrembeck-family.jpg"','src="assets/steven-schrembeck-family.jpg"')
body=re.sub(r'<h2>(.*?)</h2>',lambda m:f'<h2 id="section-{re.sub(r"[^a-z0-9]+","-",m[1].lower()).strip("-")}">{m[1]}</h2>',body)
# Preserve source wording, including its original chronology and attribution.
shutil.copy2(SRC/'memorial/READ.html',ROOT/'output/original-memorial.html')
(OUT/'downloads/memories.json').write_text(json.dumps([{k:p.get(k,'') for k in ['id','type','by','text','team','year','month','context']} for p in POSTS],ensure_ascii=False,indent=2))
GLASSES='<svg class="glasses" viewBox="0 0 64 34" fill="none" aria-hidden="true"><path d="M3 9h22l-2 16H8L3 9Zm36 0h22l-5 16H41L39 9ZM25 13c5-4 9-4 14 0M2 8 0 3m62 5 2-5" stroke="currentColor" stroke-width="3.5" stroke-linejoin="round"/></svg>'
NAV=[('explore.html','Explore'),('files.html','Downloads'),('story.html','About'),('contribute.html','Contribute')]

def page(name,title,content,active='',depth=0,description=None):
 base='../' if depth else ''
 nav=''.join(f'<a href="{base}{url}"'+(' aria-current="page"' if active==url else '')+f'>{label}</a>' for url,label in NAV)
 description=description or 'Remembering Steven Schrembeck through his words, his work, and the people whose lives he touched.'
 markup=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · Steven Schrembeck Archive</title><meta name="description" content="{e(description)}"><meta name="theme-color" content="#f8f6ef"><meta name="robots" content="index,follow"><link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{base}assets/style.css"><script src="{base}assets/app.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a><div class="wrap"><header class="site-header"><a class="brand" href="{base}index.html" aria-label="The Steven Schrembeck archive, home">{GLASSES}<span>The Steven Schrembeck Archive</span></a><button class="menu-button" aria-expanded="false" aria-controls="site-navigation">Menu</button><nav class="site-nav" id="site-navigation" aria-label="Main navigation">{nav}</nav></header><main id="main">{content}</main><footer class="site-footer"><a class="brand" href="{base}index.html">{GLASSES}<span>Steven Schrembeck · The archive</span></a><div class="footer-links"><a href="{base}explore.html">Explore</a><a href="{base}files.html">Downloads</a><a href="{base}memories.html">Memories</a></div><span>Collected with care · October 2026</span></footer></div></body></html>'''
 (OUT/name).write_text(markup)

def head(kicker,title,intro=''):
 return f'<header class="page-head"><p class="eyebrow">{kicker}</p><h1>{title}</h1>'+ (f'<p class="intro">{intro}</p>' if intro else '')+'</header>'

def quote(text,author,context):
 return f'<article class="memory-teaser"><blockquote>“{e(text)}”</blockquote><cite>{e(author)}<span>{e(context)}</span></cite></article>'


story_intro='One friend’s remembrance, part of a wider collection of memories.'

memory_cards=[]
for p in POSTS:
 kind='words' if p['type']=='words' else 'story'
 para=''.join('<p>'+e(t)+'</p>' for t in p['text'].split('\n\n'))
 text=f'<blockquote>{para}</blockquote>' if kind=='words' else f'<div class="memory-text">{para}</div>'
 context=f'<p class="context">{e(p.get("context",""))}</p>' if p.get('context') else ''
 memory_cards.append(f'<article class="memory-card" id="memory-{e(p["id"])}" data-entry data-kind="{kind}"><p class="memory-kind">'+('In Steven’s words' if kind=='words' else 'A memory')+f'</p>{text}{context}<div class="memory-author">'+('Remembered by ' if kind=='words' else '')+e(p['by'])+f'<span>{e(str(p.get("month", "")))} {e(str(p.get("year", "")))}</span></div></article>')
form='''<dialog id="memory-dialog" aria-labelledby="memory-title"><div class="dialog-top"><h2 id="memory-title">A memory worth keeping.</h2><button class="close-button" data-close-dialog aria-label="Close memory form">×</button></div><p class="small">A moment, a conversation, something that still makes you smile. Save it as a text file to keep or share with the person caring for this collection. Nothing is sent or published here.</p><form data-memory-form><label for="memory-name">Your name</label><input id="memory-name" name="name" autocomplete="name" required maxlength="120"><label for="memory-connection">How you knew Steven <span class="muted">(optional)</span></label><input id="memory-connection" name="connection" maxlength="200"><label for="memory-text">Your memory</label><textarea id="memory-text" name="memory" required maxlength="20000"></textarea><button class="button" type="submit">Download my memory <span aria-hidden="true">↓</span></button><p class="small" data-form-status role="status" style="margin-top:18px"></p></form></dialog>'''
page('memories.html','What stays with us',head('Shared by the people who knew him','What stays with us.','The encouragement. The humor. The green glasses. Memories of Steven, in the words of his friends and colleagues.')+'''<button class="button secondary js-only" data-open-dialog="memory-dialog">Write a memory <span aria-hidden="true">+</span></button><div class="searchbar js-only"><label class="visually-hidden" for="memory-search">Find a memory</label><input class="search-input" type="search" id="memory-search" placeholder="Search a name, a moment, a word…" data-search><div class="filter-buttons" aria-label="Filter memories"><button class="filter-button" data-filter="all" aria-pressed="true">All memories</button><button class="filter-button" data-filter="story" aria-pressed="false">Stories</button><button class="filter-button" data-filter="words" aria-pressed="false">Steven’s words</button></div></div><p class="results-status" data-results role="status">29 memories</p><noscript><p class="noscript-note">All memories are shown below. Your browser’s Find feature can search this page.</p></noscript><div class="memories-list">'''+''.join(memory_cards)+'''</div><div class="empty-state" data-empty hidden><h3>No memories found.</h3><p>Try a different word or name.</p><button class="button secondary" data-reset>Show all memories</button></div><p class="source-note">These 29 entries come from the supplied Cox memorial export, saved October 10, 2026. Names, wording, and contributor-assigned years are retained. Attachment screenshots and two comment replies remain in the full archive. Each contribution is one person’s recollection. The collection makes room for all of them.</p>'''+form,'memories.html')

articles=[]
for f in (SRC/'blog/pages').glob('*.txt'):
 if f.name.endswith('.headers.txt') or f.stem=='index':continue
 lines=f.read_text().splitlines()
 if 'Status' not in lines or 'Featured' not in lines:continue
 status=lines[lines.index('Status')+1]
 if status=='Unpublished':continue
 title=lines[0]; date=lines[lines.index('Created time')+1]; start=lines.index('Featured')+1
 while start<len(lines) and lines[start]=='Featured':start+=1
 desc=' '.join(lines[lines.index('Description')+1:lines.index('Featured')])
 content=[]
 for line in lines[start:]:
  if line.startswith(('✉','🔙','Copyright 2026')):break
  content.append(line)
 articles.append({'slug':f.stem,'title':title,'date':date,'description':desc,'lines':content,'sort':datetime.strptime(date,'%b %d, %Y %I:%M %p')})
 shutil.copy2(f,OUT/'downloads'/f.name)
articles.sort(key=lambda a:a['sort'],reverse=True)
for a in articles:
 mins=max(1,round(len(' '.join(a['lines']).split())/210))
 paragraphs=''.join(f'<p>{e(line)}</p>' for line in a['lines'] if line)
 page('writing/'+a['slug']+'.html',a['title'],f'''<header class="page-head article-head"><div class="breadcrumbs"><a href="../explore.html">Explore</a><span>/</span><span>A Different Compass</span></div><h1>{e(a['title'])}</h1><p class="intro">{e(a['description'])}</p><div class="article-meta"><span>By Steven Schrembeck</span><span>{a['sort'].strftime('%B %-d, %Y')}</span><span>{mins} min read</span></div></header><article class="prose article-body {'poem' if a['slug']=='to-know' else ''}">{paragraphs}<div class="source-note">A text reading copy from <em>A Different Compass</em>. Wording is retained from the saved text export; formatting has been simplified and images are not included in this reading edition. Date above is the source’s “Created time.” <a href="../downloads/{a['slug']}.txt" download>Download the original text export</a>. Full captured pages remain in the preservation archive.</div><p class="bottom-link"><a href="../explore.html?type=writing">← More from A Different Compass</a></p></article>''','explore.html',1)

recordings=[('reality/003-trailer-surprise-you-can-learn-how-it-all-works.mp3','reality-101-introduction','Reality 101','Surprise, you can learn how it all works','1 min 49 sec','reality','Steven’s introduction to his journal of experiences and explorations.'),('collected/001-reverie.mp3','reverie','Collected','Reverie','17 min 25 sec','collected','An audio story from Steven’s collection of science fiction and fantasy.'),('collected/012-mortal-steel-trailer.mp3','mortal-steel-trailer','Collected','Mortal Steel · Trailer','1 min 28 sec','collected','A first step into the world of Mortal Steel, with music, voices, and sound design.')]
jobs=json.loads((SRC/'transcripts/associations.json').read_text())['jobs']
for source,slug,series,title,duration,cover,desc in recordings:
 shutil.copy2(SRC/source,OUT/'recordings'/f'{slug}.mp3')
 job=next(j for j in jobs if j['source_path']==source)
 transcript=(SRC/job['transcript_files']['txt']).read_text()
 shutil.copy2(SRC/job['transcript_files']['txt'],OUT/'transcripts'/f'{slug}.txt')
 shutil.copy2(SRC/job['transcript_files']['vtt'],OUT/'transcripts'/f'{slug}.vtt')
 page('transcripts/'+slug+'.html',title+' — transcript',head('Recording transcript',e(title),e(series)+' · '+duration)+f'''<div class="article-body"><audio controls preload="none" style="width:100%" aria-label="{e(title)}"><source src="../recordings/{slug}.mp3" type="audio/mpeg"></audio><div class="note-panel">Machine transcription (Scribe v2), created October 10, 2026. It has not been reviewed word for word and may contain errors. The saved recording is the primary source.</div><div class="prose">{''.join('<p>'+e(t)+'</p>' for t in transcript.splitlines() if t.strip())}</div><p class="bottom-link"><a href="../explore.html?type=audio">← Back to recordings</a></p></div>''','explore.html',1)
writing_rows=''.join(f'<a class="work-row" href="writing/{a["slug"]}.html"><div><small>{a["sort"].strftime("%B %Y")} · A Different Compass</small><h3>{e(a["title"])}</h3><p>{e(a["description"])}</p></div><span aria-hidden="true">↗</span></a>' for a in articles)


shutil.copy2(SRC/'README.md',OUT/'downloads/collection-notes.txt')
(OUT/'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#f8f6ef"/><g fill="none" stroke="#3d583d" stroke-width="4" stroke-linejoin="round"><path d="M6 24h20l-2 17H10L6 24Zm32 0h20l-4 17H40l-2-17ZM26 29c4-4 8-4 12 0"/></g></svg>')
(OUT/'.nojekyll').touch()
(OUT/'robots.txt').write_text('User-agent: *\nDisallow: /\n# Local review edition. Remove alongside noindex metadata when publishing.\n')
(ROOT/'output/content-summary.json').write_text(json.dumps({'articles':len(articles),'memories':len(POSTS),'recordings':len(recordings),'photos':2,'html_pages':len(list(OUT.rglob('*.html'))),'published':False},indent=2))
(ROOT/'output/pdf-content.json').write_text(json.dumps({'story_html':body,'posts':[{k:p.get(k,'') for k in ['type','by','text','year','month','context']} for p in POSTS]},ensure_ascii=False,indent=2))
print(f'Built {len(list(OUT.rglob("*.html")))} HTML pages, {len(articles)} writings, {len(POSTS)} memories, {len(recordings)} local recordings.')
# Collective main pages; individual recollections remain individually attributed.
# Add the complete individual essay as one optional contribution in the shared collection.
p=OUT/'memories.html';s=p.read_text();s=s.replace('<p class="source-note">These 29 entries','<p class="bottom-link"><a class="text-link" href="remembrance-jeff.html">A longer remembrance by Jeff Cameron →</a></p><p class="source-note">These 29 entries');p.write_text(s)

# The archive is the primary experience. Jeff's existing memorial stays external.
import urllib.parse, email.utils
INV=json.loads((SRC/'inventory.json').read_text())
BY_PATH={x['path']:x for x in INV if x.get('path') and x.get('status')=='saved'}
(OUT/'items').mkdir(exist_ok=True)
MEDIA=[]
AUDIO=json.loads((SRC/'audio-validation.json').read_text())
VIDEOS=json.loads((SRC/'video-validation.json').read_text())
def archive_url(p):return 'collection-files/'+urllib.parse.quote(p,safe='/')
def date_from(raw):
 try:return email.utils.parsedate_to_datetime(raw).date().isoformat()
 except:return ''
def size_label(n):
 return f'{n/1024/1024:.1f} MB' if n>=1024*1024 else f'{n/1024:.0f} KB'
def item_id(p):return re.sub('[^a-z0-9]+','-',str(Path(p).with_suffix('')).lower()).strip('-')[:170]
for x in AUDIO+VIDEOS:
 p=x['path'];file=SRC/p;info={};kind='audio' if file.suffix=='.mp3' else 'video';series='';date='';basis='';origin=BY_PATH.get(p,{}).get('url','')
 if p.startswith(('reality/','collected/','interviews/')):
  metafile=file.with_suffix('.json')
  if metafile.exists():info=json.loads(metafile.read_text())
  title=info.get('title') or BY_PATH.get(p,{}).get('title') or file.stem
  series={'reality':'Reality 101','collected':'Collected','interviews':'Guest appearances'}[p.split('/')[0]]
  date=date_from(info.get('pubDate',''));basis=info.get('date_basis') or ('Feed publication date' if date else 'Date not established')
 elif p.startswith('youtube/'):
  metafile=file.with_suffix('.info.json');info=json.loads(metafile.read_text()) if metafile.exists() else {}
  title=info.get('title') or BY_PATH.get(p,{}).get('title') or file.stem
  rawdate=info.get('upload_date','');date=f'{rawdate[:4]}-{rawdate[4:6]}-{rawdate[6:]}' if len(rawdate)==8 else '';basis='YouTube upload date' if date else 'Date not established';series='Seeking Minima'
  origin=info.get('webpage_url') or ('https://www.youtube.com/watch?v='+info['id'] if info.get('id') else origin)
 else:
  info=json.loads((file.parent/'metadata.json').read_text());title=info['title'];date=info.get('recording_date','');basis='Recording date from filename and embedded metadata';series='Workplace presentations';kind='talk';origin=info.get('source_url','')
 duration=float(x.get('probe',{}).get('format',{}).get('duration',0));duration_text=f'{int(duration)//60} min {int(duration)%60:02d} sec'
 item={'id':item_id(p),'title':title,'path':p,'kind':kind,'series':series,'date':date,'date_basis':basis,'origin':origin,'size':file_size(file),'duration':duration_text,'format':file.suffix[1:].upper()}
 job=next((j for j in jobs if j.get('source_path')==p and j.get('status')=='completed'),None)
 if job:item['transcript']=job['transcript_files']['txt']
 elif info.get('transcript'):
  item['transcript']=info['transcript'];item['transcript_note']=info.get('transcript_note','Source-supplied transcript; unreviewed and may contain errors.')
 elif kind=='talk' and (file.parent/'transcript.txt').exists():item['transcript']=str((file.parent/'transcript.txt').relative_to(SRC))
 MEDIA.append(item)
WRITING=[]
for f in (SRC/'blog/pages').glob('*.txt'):
 if f.name.endswith('.headers.txt') or f.stem=='index':continue
 lines=f.read_text().splitlines()
 if 'Created time' not in lines:continue
 date=datetime.strptime(lines[lines.index('Created time')+1],'%b %d, %Y %I:%M %p').date().isoformat()
 origin=BY_PATH.get('blog/pages/'+f.stem+'.html',{}).get('url','')
 item={'id':f.stem,'title':lines[0],'path':str(f.relative_to(SRC)),'kind':'writing','series':'A Different Compass','date':date,'date_basis':'Source Created time (not a verified publication date)','origin':origin,'size':file_size(f),'format':'TXT','unpublished':lines[lines.index('Status')+1]=='Unpublished'}
 if not item['unpublished']:item['reader']='writing/'+f.stem+'.html'
 WRITING.append(item)
RELATED=json.loads((ROOT/'scripts/related-works.json').read_text())
for item in RELATED:
 item['reader']='items/'+item['id']+'.html'
 item['path']=item.get('path','')
 item['size']=file_size(SRC/item['path']) if item['path'] else 0
 item['archive_status']='saved' if item['path'] else 'link-only'
 if item['path']:BY_PATH[item['path']]={'url':item['origin']}
 links=''.join(f'<li><a href="{e(url)}">{e(label)} ↗</a></li>' for label,url in item['links'])
 player=''
 if item['path']:
  local='../'+archive_url(item['path'])
  player=f'<audio controls preload="none" style="width:100%" aria-label="{e(item["title"])}"><source src="{local}" type="audio/mpeg"></audio><p class="source-actions"><a class="button" href="{local}?download=1" download>Download saved recording ↓</a></p>'
 page(item['reader'],item['title'],head(e(item['series']),e(item['title']),e(item['note']))+f'<div class="article-body">{player}<p class="note-panel">'+('Saved recording · MP3 · '+size_label(item['size']) if item['path'] else 'Original links only · No saved copy in this archive.')+f'</p><ul class="related-links">{links}</ul><p class="source-note">{e(item["date"])} · {e(item["date_basis"])}. Source links checked October 10, 2026.</p></div>','explore.html',1)
CONTRIBUTIONS=build_contributions(SRC,page,head)
for item in CONTRIBUTIONS: BY_PATH[item['path']]={'url':item['origin']}
ITEMS=sorted(WRITING+MEDIA+RELATED+CONTRIBUTIONS,key=lambda i:(i['date'],i['title']),reverse=True)
(OUT/'downloads/catalogue.json').write_text(json.dumps(ITEMS,ensure_ascii=False,indent=2))
# Explicit original-source links also appear on each reading page and each selected recording.
for a in WRITING:
 if a.get('reader'):
  f=OUT/a['reader'];s=f.read_text();s=s.replace('<div class="article-meta">',f'<p class="source-actions"><a href="{e(a["origin"])}">Original article ↗</a><a href="../{archive_url(a["path"])}?download=1" download>Archived text ↓</a></p><div class="article-meta">');f.write_text(s)
for source,slug,*_ in recordings:
 f=OUT/'transcripts'/f'{slug}.html';s=f.read_text();orig=BY_PATH.get(source,{}).get('url','');s=s.replace('<div class="article-body">',f'<div class="article-body"><p class="source-actions"><a href="{e(orig)}">Original audio source ↗</a><a href="../{archive_url(source)}?download=1" download>Archived recording ↓</a></p>');f.write_text(s)
for item in MEDIA:
 display_date=publication_label(item) if item['kind']=='audio' else item['date'] or 'Date not established'
 date_note=item['date_basis']+('; recording date not established' if item['kind']=='audio' else '')
 local='../'+archive_url(item['path']);ext=Path(item['path']).suffix
 if item['kind']=='audio':player=f'<audio controls preload="none" style="width:100%" aria-label="{e(item["title"])}"><source src="{local}" type="audio/mpeg"></audio>'
 elif ext in ['.mp4','.webm']:player=f'<video controls preload="none" playsinline style="width:100%;max-height:65vh;background:#182018" aria-label="{e(item["title"])}"><source src="{local}" type="video/{"mp4" if ext==".mp4" else "webm"}"></video>'
 else:player='<div class="note-panel">This original recording is preserved in MKV format. Download the saved file for a compatible video player, or watch it at its original source.</div>'
 trans=''
 if item.get('transcript'):
  text=(SRC/item['transcript']).read_text(); trans=f'<details class="transcript-panel" id="transcript"><summary>Read transcript</summary><p class="small muted">'+e(item.get('transcript_note') or ('User-supplied captions; not checked word for word.' if item['kind']=='talk' else 'Machine transcription; unreviewed and may contain errors.'))+f'</p><pre>{e(text)}</pre></details>'
 source_link=f'<a class="button secondary" href="{e(item["origin"])}">Original source <span aria-hidden="true">↗</span></a>' if item['origin'] else '<span class="small muted">Original source not recorded</span>'
 page('items/'+item['id']+'.html',item['title'],f'<div class="page-head article-head"><div class="breadcrumbs"><a href="../explore.html">Explore</a><span>/</span><span>{e(item["series"])}</span></div><h1>{e(item["title"])}</h1><p class="intro">{e(item["series"])}</p><div class="article-meta"><span>{display_date}</span><span>{item["duration"]}</span><span>{item["format"]} · {size_label(item["size"])}</span></div></div>'+player+f'<div class="source-actions"><a class="button" href="{local}?download=1" download>Download archived file <span aria-hidden="true">↓</span></a>{source_link}</div>'+trans+f'<p class="source-note">Date basis: {date_note}. The saved file is a preservation copy, retained without re-encoding. Source records and checksums are available in <a href="../files.html">Downloads</a>.</p>','explore.html',1)

# A single catalogue for reading, listening, watching, and exploring.
BOOK=build_book(ROOT,OUT,page,head)
page('explore.html','Explore',head('His words · his work','Follow his curiosity.','Read an essay, listen to a story, or follow an idea. All of Steven’s collected writing, recordings, videos, presentations, and books, together in one place.')+explore_library([BOOK]+ITEMS,articles,archive_url),'explore.html')

# File browser: every retained file, including original metadata and checksum inventories.
rows=[];files=[]
for f in sorted(SRC.rglob('*')):
 if not f.is_file() or f.name=='.DS_Store':continue
 rel=str(f.relative_to(SRC));suffix=f.suffix.lower();kind='audio' if suffix=='.mp3' else 'video' if suffix in ['.mp4','.mkv','.webm'] else 'photo' if suffix in ['.jpg','.jpeg','.png','.webp'] else 'transcript' if rel.startswith('transcripts/') or suffix in ['.vtt','.srt'] else 'writing' if rel.startswith('blog/pages/') and suffix in ['.txt','.html'] and '.headers.' not in rel else 'metadata'
 source=BY_PATH.get(rel,{}).get('url','');size=file_size(f);title=next((i['title'] for i in ITEMS if i['path']==rel),f.name)
 file={'path':rel,'title':title,'kind':kind,'size':size,'source':source};files.append(file)
 original=f'<a href="{e(source)}" class="original-link">Source ↗<span class="visually-hidden">: {e(title)}</span></a>' if source else '<span class="muted">—</span>'
 rows.append(f'<tr data-entry data-kind="{kind}"><td><span class="file-title">{e(title)}</span><span class="file-path">{e(rel)}</span><span class="file-original-mobile">{original}</span></td><td>{suffix[1:].upper() or "FILE"}</td><td>{size_label(size)}</td><td>{original}</td><td><a class="file-download" href="{archive_url(rel)}?download=1" download aria-label="Download {e(f.name)}">Download ↓</a></td></tr>')
(OUT/'downloads/file-inventory.json').write_text(json.dumps(files,ensure_ascii=False,indent=2))
downloads_intro = '''<section class="download-options" aria-label="Collection downloads"><article class="download-card"><p class="eyebrow">Everything, together</p><h2>The complete collection.</h2><p>Saved works, photographs, transcripts, source notes, and an offline edition of the website. Approximately 5 GB.</p><a class="button" href="downloads/steven-schrembeck-complete.zip" download>Download the complete archive ↓</a><p class="small download-help">ZIP64 · Extract, then open START-HERE.html</p><a class="text-link" href="https://github.com/jcameronjeff/steven-schrembeck-memorial/releases">Get a copy from GitHub Releases ↗</a></article><article class="download-card"><p class="eyebrow">Memories &amp; care</p><h2>A collection to pass on.</h2><p>Keep the memories shared by friends and colleagues, along with instructions for opening, checking, and caring for the files.</p><div class="download-support"><a class="text-link" href="downloads/remembering-steven.pdf" download>Shared memories · PDF ↓</a><a class="text-link" href="downloads/CARETAKER-GUIDE.txt" download>Caretaker guide · TXT ↓</a><a class="text-link" href="downloads/collection-notes.txt">Original collection notes →</a></div></article></section><div class="section-heading downloads-heading"><div><p class="eyebrow">One thing at a time</p><h2>Individual downloads.</h2></div><a class="text-link" href="explore.html">Read, listen &amp; explore →</a></div>'''
page('files.html','Downloads',head('Keep what speaks to you','Yours to keep.','Save the complete collection or choose individual works. Recordings, writing, photographs, and supporting files are preserved in their original formats.')+book_download_card()+downloads_intro+'''<div class="searchbar js-only"><label class="visually-hidden" for="files-search">Search files</label><input class="search-input" type="search" id="files-search" placeholder="Search a title or filename…" data-search><select aria-label="File type" data-kind-select><option value="all">All files</option><option value="audio">Audio</option><option value="video">Video</option><option value="writing">Writing</option><option value="photo">Photographs &amp; artwork</option><option value="transcript">Transcripts</option><option value="metadata">Source notes &amp; metadata</option></select></div>'''+f'<p class="results-status" data-results data-noun="files" role="status">{len(files)} files · {sum(f["size"] for f in files)/1e9:.2f} GB</p><div class="files-table-wrap"><table class="files-table"><thead><tr><th scope="col">File</th><th scope="col">Format</th><th scope="col">Size</th><th scope="col">Original</th><th scope="col"><span class="visually-hidden">Download</span></th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><div class="empty-state" data-empty hidden><h3>No files found.</h3><button class="button secondary" data-reset>Show all files</button></div><p class="source-note">Original links are shown where recorded in the retrieval inventory. Supporting metadata and generated transcripts may have no independent source URL. Archived HTML downloads are source files and may refer to online assets; use the reading pages for the self-contained text edition.</p>','files.html')
# Revised landing page: archive first, no retelling of Jeff's post.
page('index.html','The Steven Schrembeck archive',f'''<section class="hero" aria-labelledby="hero-title"><div><p class="eyebrow">The Steven Schrembeck archive</p><h1 id="hero-title"><span>Steven</span><span>Schrembeck.</span></h1><p class="hero-subtitle">His words. His work.<br>A place to return to.</p><div class="hero-actions"><a class="button" href="explore.html">Explore his work <span aria-hidden="true">↗</span></a><a class="text-link" href="story.html">About Steven <span aria-hidden="true">→</span></a></div><p class="hero-note">For everyone who knew him.<br>And everyone who has yet to discover him.</p></div><figure class="hero-photo"><img src="assets/steven-schrembeck-family.jpg" alt="Steven with Amanda and their two sons by the ocean" width="720" height="407" fetchpriority="high"><figcaption class="caption"><span>Steven, Amanda, and their boys.</span><a href="photos.html">The photographs ↗</a></figcaption></figure></section><nav class="routes" aria-label="Explore the collections"><a class="route" href="explore.html?type=writing"><span class="route-num">01</span><span><span class="route-title">Read his writing</span><span class="route-sub">A Different Compass</span></span><span class="arrow" aria-hidden="true">↗</span></a><a class="route" href="explore.html?type=audio"><span class="route-num">02</span><span><span class="route-title">Hear his voice</span><span class="route-sub">Podcasts, stories, and conversations</span></span><span class="arrow" aria-hidden="true">↗</span></a><a class="route" href="explore.html?type=video"><span class="route-num">03</span><span><span class="route-title">See his ideas</span><span class="route-sub">Seeking Minima and beyond</span></span><span class="arrow" aria-hidden="true">↗</span></a></nav><section class="section"><div class="section-heading"><div><p class="eyebrow">Begin anywhere</p><h2>A mind worth exploring.</h2></div><a class="text-link" href="explore.html">The complete collection →</a></div><div class="work-list"><a class="work-row" href="writing/it-s-connection.html"><div><small>A Different Compass · October 2025</small><h3>It’s Connection</h3><p>A piece of writing to begin with.</p></div><span aria-hidden="true">↗</span></a><a class="work-row" href="items/{item_id('collected/001-reverie.mp3')}.html"><div><small>Collected · Audio fiction</small><h3>Reverie</h3><p>Step into an imagined world.</p></div><span aria-hidden="true">↗</span></a><a class="work-row" href="explore.html?type=video"><div><small>Seeking Minima · 22 saved videos</small><h3>Questions worth following</h3><p>Technology, meaning, and being human.</p></div><span aria-hidden="true">↗</span></a><a class="work-row" href="book.html"><div><small>A book drawn from the recordings</small><h3>The Small Moments Are Everything</h3><p>Read the compiled book, chapter by chapter.</p></div><span aria-hidden="true">↗</span></a></div></section><section class="voice"><div><p class="eyebrow">In his own voice</p><h2>Spend a little time<br>with Steven.</h2><p>Listen to his introduction to Reality 101. The saved recording is right here, with its original source and transcript.</p><a class="text-link" href="explore.html?type=audio">Explore the recordings →</a></div><div class="voice-player"><div class="recording"><img src="assets/reality-cover.jpg" alt="Reality 101 artwork" width="72" height="72"><div><small>REALITY 101 · INTRODUCTION</small><h3>Surprise, you can learn how it all works</h3><small>1 min 49 sec</small></div></div><audio controls preload="none" aria-label="Reality 101 introduction"><source src="recordings/reality-101-introduction.mp3" type="audio/mpeg"></audio><p class="audio-note"><a href="items/{item_id('reality/003-trailer-surprise-you-can-learn-how-it-all-works.mp3')}.html">Saved file, original source &amp; transcript →</a></p></div></section><section class="section story-grid"><div><p class="eyebrow">Behind the work</p><h2 style="margin-top:16px">A different way<br>of seeing.</h2><div class="portrait-label"><img src="assets/steven-schrembeck.jpg" alt="Steven in his green glasses" width="62" height="62" loading="lazy"><div>Engineer. Writer. Storyteller.<span>Husband, father, and friend.</span></div></div></div><div class="story-prose"><p>Steven was a UI developer and Principal Engineer at Cox Automotive. Beyond software, he wrote, made audio fiction, recorded podcasts, and shared explorations on video.</p><p>This archive brings those pieces together, so his family, friends, colleagues, and future readers can keep discovering the things he made.</p><a class="text-link" href="story.html">About Steven →</a></div></section><section class="preserve"><div><p class="eyebrow" style="margin-bottom:12px">Made to be kept</p><h2>Find a file. Keep a piece.</h2><p>Download individual works or keep a complete copy. Original sources remain alongside the saved files.</p></div><a class="button secondary" href="files.html">Browse downloads <span aria-hidden="true">↓</span></a></section>''')
page('story.html','About Steven',head('The person behind the work','About Steven.','Engineer. Writer. Storyteller. Husband, father, and friend.')+'''<div class="reading-layout"><aside class="reading-sidebar"><img src="assets/steven-schrembeck.jpg" alt="Steven in his green glasses" width="260" height="227"><p style="margin-top:14px">Steven Schrembeck</p></aside><article class="prose"><p>Steven Schrembeck was a UI developer and Principal Engineer at Cox Automotive. He was Amanda’s husband and a father to their two sons. He passed away in September 2026.</p><p>His creative work ranged across essays, podcasts, audio fiction, and video. <em>A Different Compass</em>, <em>Reality 101</em>, <em>Collected</em>, and <em>Seeking Minima</em> are different ways into his interests and imagination.</p><h2>A home for the work.</h2><p>This archive brings together saved copies of the things he made and shared, alongside links to their original sources. It is for his family, for the people who knew him, and for anyone who finds something here worth spending time with.</p><p><a href="explore.html">Explore the collection →</a></p><h2>Remembering the person.</h2><p>The people who knew Steven have their own stories to tell. Their remembrances belong to them, and help put the work in context.</p><div class="remembrance-link"><p class="eyebrow">A personal remembrance</p><h3><a href="https://remembering-steven-schrembeck.opzero.sh/">Remembering Steven Schrembeck ↗</a></h3><p class="small muted">By Jeff Cameron · Read the original post</p></div><p><a href="memories.html">Memories shared by friends and colleagues →</a></p><div class="source-note">Biographical details come from the original memorial and supplied collection. This introduction does not attempt a complete biography.</div></article></div>''','story.html')
# Keep Jeff's first-person post linked, not re-quoted in the archive's editorial pages.
p=OUT/'memories.html';s=p.read_text()
for post in POSTS:
 if post['by'] in ['Jeff Cameron','Jefe']:
  s=re.sub(r'<article class="memory-card" id="memory-'+re.escape(post['id'])+r'".*?</article>','',s,flags=re.S)
count=sum(p['by'] not in ['Jeff Cameron','Jefe'] for p in POSTS)
s=s.replace('29 memories',f'{count} memories').replace('href="remembrance-jeff.html"','href="https://remembering-steven-schrembeck.opzero.sh/"').replace('A longer remembrance by Jeff Cameron →','Read Jeff Cameron’s original remembrance ↗')
s=re.sub(r'These 29 entries come from.*?</p>',f'These {count} entries are from friends and colleagues in the supplied memorial export. Contributor wording is retained. Jeff Cameron’s remembrance is linked above; the complete original export remains in the preservation files.</p>',s,flags=re.S);p.write_text(s)
(OUT/'remembrance-jeff.html').unlink(missing_ok=True)
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n')
(ROOT/'output/content-summary.json').write_text(json.dumps({'works':len(ITEMS),'writings':len(WRITING),'reading_pages':len(articles),'audio_recordings':len(AUDIO)+sum(bool(i['path']) and i['kind']=='audio' for i in RELATED),'link_only':sum(not i['path'] for i in RELATED),'videos':len(VIDEOS),'files':len(files),'bytes':sum(f['size'] for f in files)},indent=2))
print('Full archive catalogue:',len(ITEMS),'works;',len(files),'preservation files')
(OUT/'photos.html').unlink(missing_ok=True)
for p in OUT.rglob('*.html'):
 s=p.read_text().replace('href="photos.html"','href="files.html?type=photo"').replace('The photographs ↗','Save the photographs ↓')
 p.write_text(s)
# The download browser opens on the works themselves, with technical files optional.
p=OUT/'files.html';s=p.read_text().replace('<option value="all">All files</option>','<option value="featured">Works &amp; photographs</option><option value="all">Every preservation file</option>')
for item in ITEMS:
 marker=f'<span class="file-path">{e(item["path"])}</span>'
 pos=s.find(marker)
 if pos>=0:
  before=s.rfind('<tr data-entry',0,pos);s=s[:before]+s[before:].replace('<tr data-entry','<tr data-entry data-main="true"',1)
for name in ['steven-schrembeck.jpg','steven-schrembeck-family.jpg']:
 pos=s.find(f'<span class="file-path">memorial/{name}</span>');before=s.rfind('<tr data-entry',0,pos)
 if pos>=0:s=s[:before]+s[before:].replace('<tr data-entry','<tr data-entry data-main="true"',1)
p.write_text(s)
for p in OUT.rglob('*.html'):
 s=p.read_text().replace(' · Steven Schrembeck Archive</title>',' · Steven Schrembeck Archive</title>');p.write_text(s)
# Forward old bookmarks; every active link uses Explore or Downloads.
redirects = {'collection.html': 'explore.html', 'work.html': 'explore.html',
             'timeline.html': 'explore.html?sort=oldest', 'archive.html': 'files.html'}
for old, target in redirects.items():
 page(old,'Page moved',head('The collection, simplified','A new place to begin.')+f'<p><a href="{target}">Continue to {"Downloads" if target == "files.html" else "Explore"} →</a></p>')
 p=OUT/old
 s=p.read_text().replace('<meta name="robots" content="index,follow">','<meta name="robots" content="noindex,follow">')
 script = f"const next = new URL({json.dumps(target)}, location.href); for (const [key, value] of new URLSearchParams(location.search)) next.searchParams.set(key, value); if (location.hash === '#listen') next.searchParams.set('type', 'audio'); if (location.hash === '#writing') next.searchParams.set('type', 'writing'); location.replace(next.href);"
 s=s.replace('</head>',f'<script>{script}</script><noscript><meta http-equiv="refresh" content="0;url={target}"></noscript></head>')
 p.write_text(s)

# The upload page is enhanced by the bundled client on Vercel.
build_form(page,head)
