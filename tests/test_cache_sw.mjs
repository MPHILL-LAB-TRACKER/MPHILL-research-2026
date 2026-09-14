/** Behavioral tests for the generated public-only Service Worker; no network used. */
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const code = fs.readFileSync(new URL('../public/assets/sw-template.js', import.meta.url), 'utf8');
let count=0;
function check(value,label){assert.ok(value,label);console.log('PASS '+label);count++;}
function harness(overrides={}) {
 const listeners={},stores=new Map(), config={enabled:true,prefix:'/lab/',namespace:'ted2-lab-',cache:'ted2-lab-new',limit:2,...overrides};
 let calls=0,failOpen=false,failPut=false,privateResponse=false,length=10;
 const reply=()=>({ok:true,type:'basic',headers:new Headers({'Content-Length':String(length),'Cache-Control':privateResponse?'private, no-store':'public, max-age=31536000, immutable'}),clone(){return this;}});
 const caches={keys:async()=>[...stores.keys()],delete:async name=>stores.delete(name),open:async name=>{
  if(failOpen)throw Error('blocked');if(!stores.has(name))stores.set(name,new Map());const map=stores.get(name);
  return {match:async req=>map.get(req.url),put:async(req,res)=>{if(failPut)throw Error('quota');map.set(req.url,res);},keys:async()=>[...map.keys()].map(url=>new Request(url)),delete:async req=>map.delete(req.url)};
 }};
 const context=vm.createContext({C:config,URL,Headers,Request,caches,fetch:async()=>{calls++;return reply();},self:{location:{origin:'https://example.org'},addEventListener:(name,fn)=>listeners[name]=fn,skipWaiting(){},clients:{claim:async()=>{}}}});
 vm.runInContext(code,context);
 async function request(path,options={}){let result;const event={request:new Request(path.startsWith('https:')?path:'https://example.org'+path,options),respondWith(p){result=p;}};listeners.fetch(event);return result===undefined?{handled:false}:{handled:true,response:await result};}
 async function activate(){let p;listeners.activate({waitUntil(value){p=value;}});await p;}
 return {request,activate,stores,get calls(){return calls;},set failOpen(v){failOpen=v;},set failPut(v){failPut=v;},set privateResponse(v){privateResponse=v;},set length(v){length=v;}};
}
const image='/lab/public-media/'+'a'.repeat(64)+'.jpg';
const h=harness();
for(const path of ['/lab/','/lab/admin','/lab/api/bootstrap','/lab/workspace','/lab/questions/','/lab/science-feed.json','/lab/sw.js','/lab/assets/site.css','/lab/public-media/'+'b'.repeat(64)+'.pdf','/lab/public-media/'+'b'.repeat(64)+'.mp4','/other/assets/site.css?v=0123456789abcdef','https://other.org/lab/assets/site.css?v=0123456789abcdef'])check(!(await h.request(path)).handled,'Bypass private/non-versioned/non-image route '+path);
check(!(await h.request(image,{method:'POST'})).handled,'POST requests bypass cache');
check(!(await h.request(image,{headers:{range:'bytes=0-9'}})).handled,'Range requests bypass cache');
check((await h.request(image)).handled&&h.calls===1,'First immutable image request uses network');
check((await h.request(image)).handled&&h.calls===1,'Second immutable image request uses cached response');
await h.request('/lab/assets/site.css?v=0123456789abcdef');await h.request('/lab/assets/site.js?v=0123456789abcdef');
check(h.stores.get('ted2-lab-new').size===2,'Cache entries are bounded by administrator limit');
check(!h.stores.get('ted2-lab-new').has('https://example.org'+image),'Oldest public asset is evicted');
h.stores.set('ted2-lab-old',new Map());h.stores.set('unrelated-site-cache',new Map());await h.activate();
check(!h.stores.has('ted2-lab-old')&&h.stores.has('ted2-lab-new'),'Activation removes only old release generations');
check(h.stores.has('unrelated-site-cache'),'Other applications caches are preserved');
const disabled=harness({enabled:false});disabled.stores.set('ted2-lab-old',new Map());await disabled.activate();
check(!disabled.stores.size&&!(await disabled.request(image)).handled,'Disabled caching cleans its own cache and bypasses fetch');
const priv=harness();priv.privateResponse=true;await priv.request(image);await priv.request(image);check(priv.calls===2,'Private/no-store responses never enter CacheStorage');
const large=harness();large.length=1048577;await large.request(image);await large.request(image);check(large.calls===2,'Oversized public responses are not stored');
const blocked=harness();blocked.failOpen=true;check((await blocked.request(image)).response.ok&&blocked.calls===1,'Blocked CacheStorage falls back to network');
const quota=harness();quota.failPut=true;check((await quota.request(image)).response.ok,'Cache quota failures do not break valid network responses');
console.log(`\n${count} Service Worker behavior checks passed.`);
