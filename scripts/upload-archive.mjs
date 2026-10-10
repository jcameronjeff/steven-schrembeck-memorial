import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const source=path.resolve(root,'collection');
const host=process.env.ARCHIVE_UPLOAD_URL || JSON.parse(fs.readFileSync(path.join(root,'output/media-host.json'))).url;
const token=process.env.ARCHIVE_UPLOAD_TOKEN || fs.readFileSync(path.join(root,'.private/upload-token'),'utf8');
const report=path.join(root,'output/upload-log.jsonl');
const done=new Map(fs.existsSync(report)?fs.readFileSync(report,'utf8').trim().split('\n').filter(Boolean).map(s=>{const a=JSON.parse(s);return[a.path,a]}):[]);
const types={'.html':'text/html;charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.jsonl':'application/x-ndjson','.txt':'text/plain;charset=utf-8','.md':'text/plain;charset=utf-8','.csv':'text/csv','.xml':'application/xml','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.mp4':'video/mp4','.webm':'video/webm','.mkv':'video/x-matroska','.vtt':'text/vtt','.pdf':'application/pdf','.zip':'application/zip','.tar':'application/x-tar'};
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.name==='.DS_Store'?[]:e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const jobs=process.argv[2]==='--manifest'?JSON.parse(fs.readFileSync(process.argv[3],'utf8')):process.argv[2]?process.argv.slice(2).map(f=>({local:path.resolve(f),key:'downloads/'+path.basename(f)})):walk(source).map(local=>({local,key:path.relative(source,local)}));
const chunk=8*1024*1024;
async function call(key,method,body,extra={},q=''){
 for(let attempt=0;attempt<5;attempt++){
  try{
   const r=await fetch(host+'/'+key.split('/').map(encodeURIComponent).join('/')+q,{method,headers:{Authorization:`Bearer ${token}`,...extra},body,signal:AbortSignal.timeout(180000)});
   const text=await r.text();if(!r.ok)throw Error(`${r.status}: ${text.slice(0,250)}`);return text?JSON.parse(text):{};
  }catch(e){if(attempt===4)throw e;await new Promise(r=>setTimeout(r,1000*(attempt+1)));}
 }
}
let finished=0,total=jobs.length;
async function upload(job){
 const size=fs.statSync(job.local).size;const hash=crypto.createHash('sha256');for await(const b of fs.createReadStream(job.local))hash.update(b);const sha=hash.digest('hex');
 if(done.get(job.key)?.sha256===sha&&done.get(job.key)?.size===size){finished++;return;}
 const mime=types[path.extname(job.local).toLowerCase()]||'application/octet-stream';
 if(size<=chunk){let b=fs.readFileSync(job.local);await call(job.key,'PUT',b,{'content-type':mime,'x-content-sha256':sha});}
 else{
  const {uploadId}=await call(job.key,'POST',JSON.stringify({contentType:mime,sha256:sha}),{'content-type':'application/json'},'?action=create');
  const parts=[];let fd=fs.openSync(job.local,'r');
  try{
   for(let offset=0,number=1;offset<size;offset+=chunk,number++){
    const b=Buffer.alloc(Math.min(chunk,size-offset));fs.readSync(fd,b,0,b.length,offset);let digest=crypto.createHash('sha256').update(b).digest('hex');
    const part=await call(job.key,'PUT',b,{'content-type':mime,'x-content-sha256':digest},`?action=part&uploadId=${encodeURIComponent(uploadId)}&partNumber=${number}`);parts.push(part);
   }
   const result=await call(job.key,'POST',JSON.stringify({parts}),{'content-type':'application/json'},`?action=complete&uploadId=${encodeURIComponent(uploadId)}`);if(result.size!==size)throw Error('Final size mismatch');
  }catch(err){await call(job.key,'DELETE',undefined,{},`?action=abort&uploadId=${encodeURIComponent(uploadId)}`).catch(()=>{});throw err;}finally{fs.closeSync(fd);}
 }
 const r=await fetch(host+'/'+job.key.split('/').map(encodeURIComponent).join('/'),{method:'HEAD'});if(!r.ok||Number(r.headers.get('content-length'))!==size||r.headers.get('x-archive-sha256')!==sha)throw Error('Read-after-write verification failed: '+job.key);
 const item={path:job.key,size,sha256:sha,verified:true};fs.appendFileSync(report,JSON.stringify(item)+'\n');finished++;
 if(size>1000000||finished%50===0)console.log(`${finished}/${total} verified ${job.key} (${(size/1048576).toFixed(1)} MB)`);
}
// Largest uploads begin first; independent files use four bounded workers.
jobs.sort((a,b)=>fs.statSync(b.local).size-fs.statSync(a.local).size);
let cursor=0;await Promise.all(Array.from({length:4},async()=>{while(cursor<jobs.length){const j=jobs[cursor++];await upload(j);}}));
console.log(JSON.stringify({complete:true,files:jobs.length,verified:finished}));
