// This prefix is the complete authority of this Worker. It never accepts an R2 key.
const PREFIX='memorial/steven-schrembeck-archive-20261010/';
const json=(data,status=200)=>Response.json(data,{status});
function relative(path){let p;try{p=decodeURIComponent(path).replace(/^\/+/, '');}catch{return null;}if(!p||p.split('/').some(x=>x==='..'||x==='.'||!x)||/[\x00-\x1f\\]/.test(p))return null;return p;}
export async function serve(request,env,path){
 if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405,headers:{Allow:'GET, HEAD'}});
 const p=relative(path);if(!p)return new Response('Not found',{status:404});
 const key=PREFIX+p;
 const head=await env.ARCHIVE.head(key);if(!head)return new Response('Not found',{status:404});
 const headers=new Headers();head.writeHttpMetadata(headers);
 headers.set('ETag',head.httpEtag);headers.set('Accept-Ranges','bytes');headers.set('X-Content-Type-Options','nosniff');headers.set('Cache-Control','public, max-age=3600');
 headers.set('X-Archive-SHA256',head.customMetadata?.sha256||'');
 if(new URL(request.url).searchParams.has('download')||p.endsWith('.html')||p.endsWith('.js')||p.endsWith('.svg')){headers.set('Content-Disposition',`attachment; filename*=UTF-8''${encodeURIComponent(p.split('/').pop())}`);headers.set('Content-Security-Policy',"sandbox; default-src 'none'");}
 if(request.headers.get('If-None-Match')===head.httpEtag)return new Response(null,{status:304,headers});
 let range=null;const raw=request.headers.get('Range');
 if(raw){const m=/^bytes=(\d*)-(\d*)$/.exec(raw);if(!m||(!m[1]&&!m[2])){headers.set('Content-Range',`bytes */${head.size}`);return new Response(null,{status:416,headers});}
 let start=m[1]?Number(m[1]):Math.max(0,head.size-Number(m[2]));let end=m[1]?(m[2]?Math.min(Number(m[2]),head.size-1):head.size-1):head.size-1;
 if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>=head.size||end<start){headers.set('Content-Range',`bytes */${head.size}`);return new Response(null,{status:416,headers});}
 range={offset:start,length:end-start+1};headers.set('Content-Range',`bytes ${start}-${end}/${head.size}`);headers.set('Content-Length',String(range.length));
 }else headers.set('Content-Length',String(head.size));
 if(request.method==='HEAD')return new Response(null,{status:range?206:200,headers});
 const object=await env.ARCHIVE.get(key,range?{range}:undefined);
 return new Response(object?.body||null,{status:range?206:200,headers});
}
