import {serve} from '../hosting/serve-r2.mjs';
export default {async fetch(request,env){
 const url=new URL(request.url);
 if(['/downloads/steven-schrembeck-complete.zip','/downloads/steven-schrembeck-complete.zip.sha256'].includes(url.pathname)){
  url.searchParams.set('download','1');
  return serve(new Request(url,request),env,url.pathname.slice(1));
 }
 if(url.pathname.startsWith('/collection-files/'))return serve(request,env,url.pathname.slice('/collection-files/'.length));
 return env.ASSETS.fetch(request);
}};
