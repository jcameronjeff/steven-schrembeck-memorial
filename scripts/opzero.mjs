import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
const config=JSON.parse(fs.readFileSync(path.join(os.homedir(),'.opzero/config.json'),'utf8'));
const [method='tools/list',name,argfile]=process.argv.slice(2);
const args=argfile?JSON.parse(fs.readFileSync(argfile,'utf8')):{};
const body={jsonrpc:'2.0',id:1,method,...(name?{params:{name,arguments:args}}:{})};
const response=await fetch('https://opzero.sh/mcp',{method:'POST',headers:{'Authorization':`Bearer ${config.auth.apiKey}`,'Content-Type':'application/json','Accept':'application/json, text/event-stream'},body:JSON.stringify(body)});
const raw=await response.text();let data;
try{data=JSON.parse(raw);}catch{const line=raw.split('\n').find(l=>l.startsWith('data: '));data=line?JSON.parse(line.slice(6)):{status:response.status,message:raw.slice(0,400)};}
if(method==='tools/list'){
 fs.writeFileSync(new URL('../output/opzero-tools.json',import.meta.url),JSON.stringify(data,null,2));
 console.log(JSON.stringify({status:response.status,tools:data.result?.tools?.filter(t=>/deploy_files|get_project_details|blob|upload|domain/.test(t.name))||data},null,2));
}else console.log(JSON.stringify(data,null,2));
