const fs=require('fs'),vm=require('vm'),assert=require('assert');
const root='/Users/opz/Documents/Codex/2026-10-10/i/outputs/steven-schrembeck-archive/transcripts/';
class Element {constructor(){this.children=[];this.textContent='';this.value='';this.handlers={};}append(...nodes){this.children.push(...nodes)}replaceChildren(...nodes){this.children=nodes}addEventListener(k,f){this.handlers[k]=f}}
const ids=Object.fromEntries(['q','results','status'].map(k=>[k,new Element()]));
const context=vm.createContext({document:{getElementById:k=>ids[k],createElement:()=>new Element()}});
vm.runInContext(fs.readFileSync(root+'search-data.js','utf8'),context);
const html=fs.readFileSync(root+'index.html','utf8');const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
vm.runInContext(script,context);
const total=vm.runInContext('TRANSCRIPTS.length',context);assert.equal(ids.results.children.length,total);
for(const term of ['planescarred','Mortal Steel','deep meaning','zzzznomatchzzzz','']){ids.q.value=term;ids.q.handlers.input();const expected=vm.runInContext(`TRANSCRIPTS.filter(r=>r.text.toLowerCase().includes(${JSON.stringify(term.toLowerCase())})||r.title.toLowerCase().includes(${JSON.stringify(term.toLowerCase())})).length`,context);assert.equal(ids.results.children.length,expected);console.log(JSON.stringify({query:term,results:expected}));}
console.log('Offline search logic passes; no browser rendering or network used.');
