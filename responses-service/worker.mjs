/** TED2 response gateway. Original implementation. No GitHub, lab-db or Overleaf credentials. */
const enc=new TextEncoder();
const hex=bytes=>Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join('');
const random=n=>hex(crypto.getRandomValues(new Uint8Array(n)));
const hash=async text=>hex(await crypto.subtle.digest('SHA-256',enc.encode(text)));
async function mac(secret,text){const key=await crypto.subtle.importKey('raw',enc.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);return hex(await crypto.subtle.sign('HMAC',key,enc.encode(text)));}
function check(ok,status,message){if(!ok)throw Object.assign(new Error(message),{status});}
async function equal(a,b){return (await hash(a))===(await hash(b));}
async function jsonBody(request){
 check(Number(request.headers.get('content-length')||0)<=16384,413,'Message too large.');
 check((request.headers.get('content-type')||'').startsWith('application/json'),415,'Use JSON.');
 check(request.body,422,'A JSON object is required.');const reader=request.body.getReader();let size=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>16384){await reader.cancel();check(false,413,'Message too large.');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.byteLength;}
 let body;try{body=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}catch{check(false,422,'Invalid JSON.');}
 check(body&&typeof body==='object'&&!Array.isArray(body),422,'An object is required.');return body;
}
function field(b,k,min,max){const text=b[k]??'';check(typeof text==='string',422,`Use text in ${k}.`);const v=text.trim();check(v.length>=min&&enc.encode(v).length<=max&&!/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(v),422,`${k} is missing or too long.`);return v;}
function validOrigin(o){try{const u=new URL(o);return u.protocol==='https:'&&u.origin===o&&!u.username&&!u.password&&!u.port;}catch{return false;}}
async function rate(env,request,kind,max,window=3600){const now=Math.floor(Date.now()/1000),ip=request.headers.get('CF-Connecting-IP')||'unavailable';const key=await mac(env.ADMIN_TOKEN,`${kind}|${ip}|${Math.floor(now/window)}`);
 await env.DB.prepare('DELETE FROM limits WHERE expires < ?').bind(now).run();
 await env.DB.prepare('INSERT INTO limits VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1').bind(key,now+window).run();
 const row=await env.DB.prepare('SELECT count FROM limits WHERE key=?').bind(key).first();check(row.count<=max,429,'Too many requests. Try again later.');}
function response(data,status,origin){const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Vary':'Origin'};if(origin)headers['Access-Control-Allow-Origin']=origin;return new Response(JSON.stringify(data),{status,headers});}
async function config(env){const row=await env.DB.prepare("SELECT value FROM settings WHERE key='configuration'").first();return row?JSON.parse(row.value):{enabled:false,origin:'',researchers:[]};}
export async function handle(request,env){let cors='';try{
 check(/^[a-f0-9]{64}$/.test(env.ADMIN_TOKEN||''),503,'Service setup is incomplete.');
 const url=new URL(request.url),path=url.pathname,method=request.method;
 if(path.startsWith('/admin/')){
  const token=(request.headers.get('Authorization')||'').replace(/^Bearer /,'');check(token.length===64&&await equal(token,env.ADMIN_TOKEN),401,'Invalid response-service administrator key.');
  if(path==='/admin/config'&&method==='PUT'){
   const b=await jsonBody(request);check(validOrigin(b.origin),422,'Use an HTTPS public website origin.');check(typeof b.enabled==='boolean'&&Array.isArray(b.researchers)&&b.researchers.length<=200,422,'Invalid configuration.');
   const preview=b.preview_origin||'';check(preview===''||/^http:\/\/(?:127\.0\.0\.1|localhost)(?::[0-9]{1,5})?$/.test(preview),422,'Invalid local preview origin.');
   const researchers=b.researchers.map(p=>{check(p&&typeof p.id==='string'&&/^[a-z0-9][a-z0-9-]{0,79}$/.test(p.id)&&typeof p.name==='string'&&p.name.length<=180,422,'Invalid researcher option.');return {id:p.id,name:p.name};});
   await env.DB.prepare("INSERT INTO settings VALUES ('configuration',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(JSON.stringify({enabled:b.enabled,origin:b.origin,preview_origin:preview,researchers})).run();return response({ok:true},200,'');
  }
  if(path==='/admin/messages'&&method==='GET'){const rows=await env.DB.prepare('SELECT id,researcher_id,subject,message,nickname,consent_public,reply,status,created_at,updated_at FROM messages ORDER BY created_at DESC LIMIT 200').all();return response({items:rows.results},200,'');}
  const match=path.match(/^\/admin\/messages\/([a-f0-9]{32})$/);if(match){
   const p=await env.DB.prepare('SELECT * FROM messages WHERE id=?').bind(match[1]).first();check(p,404,'Message not found.');const b=await jsonBody(request);
   if(method==='DELETE'){check(b.confirm==='DELETE',422,'Confirm deletion.');await env.DB.prepare('DELETE FROM messages WHERE id=?').bind(match[1]).run();return response({ok:true},200,'');}
   if(method==='PUT'){const reply=field(b,'reply',0,8000);check(['pending','answered','public','closed'].includes(b.status),422,'Invalid response status.');check(!['answered','public'].includes(b.status)||reply.length>=2,422,'Write a reply first.');check(b.status!=='public'||p.consent_public===1,422,'The visitor did not consent to public sharing.');await env.DB.prepare('UPDATE messages SET reply=?,status=?,updated_at=? WHERE id=?').bind(reply,b.status,new Date().toISOString(),match[1]).run();return response({ok:true},200,'');}
  }
  check(false,404,'Admin operation not found.');
 }
 const c=await config(env),origin=request.headers.get('Origin')||'';cors=origin&&(origin===c.origin||origin===c.preview_origin)?origin:'';
 if(method==='OPTIONS'){check(cors,403,'Origin not allowed.');return new Response(null,{status:204,headers:{'Access-Control-Allow-Origin':cors,'Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600','Vary':'Origin'}});}
 if(path==='/api/community/health'&&method==='GET')return response({ok:true,service:'TED2 Responses',version:'1',enabled:c.enabled,moderated:true},200,cors);
 check(c.enabled,403,'Visitor responses are closed.');
 if(path==='/api/community/public'&&method==='GET'){const rows=await env.DB.prepare("SELECT id,researcher_id,subject,message,nickname,reply,updated_at FROM messages WHERE status='public' AND consent_public=1 ORDER BY updated_at DESC LIMIT 40").all();return response({items:rows.results},200,cors);}
 if(path==='/api/community/challenge'&&method==='GET'){check(cors,403,'Open the form on the configured website.');await rate(env,request,'challenge',60);const value=`${Math.floor(Date.now()/1000)}.${random(16)}`;return response({token:`${value}.${await mac(env.ADMIN_TOKEN,value)}`,wait_seconds:2},200,cors);}
 check(method==='POST'&&cors,403,'Open the form on the configured website.');const b=await jsonBody(request);
 if(path==='/api/community/submit'){
  await rate(env,request,'submit',8);const m=typeof b.token==='string'&&b.token.match(/^(\d{10})\.([a-f0-9]{32})\.([a-f0-9]{64})$/);check(m,403,'Reload the form.');const age=Math.floor(Date.now()/1000)-Number(m[1]);check(age>=2&&age<=1800&&await equal(m[3],await mac(env.ADMIN_TOKEN,`${m[1]}.${m[2]}`)),403,'Wait two seconds after opening the form, or reload it.');check(!b.website,422,'Submission rejected.');
  const subject=field(b,'subject',3,180),message=field(b,'message',8,4000),nickname=field(b,'nickname',0,80),rid=field(b,'researcher_id',0,80);
  check(!rid||c.researchers.some(p=>p.id===rid),422,'Choose a published researcher or General laboratory.');check(typeof (b.consent_public??false)==='boolean',422,'Invalid sharing permission.');
  const n=await env.DB.prepare('SELECT COUNT(*) n FROM messages').first();check(n.n<5000,503,'Inbox capacity reached. Use the published contact details.');
  await env.DB.prepare('DELETE FROM used_challenges WHERE expires<?').bind(Math.floor(Date.now()/1000)).run();
  try{await env.DB.prepare('INSERT INTO used_challenges VALUES (?,?)').bind(await hash(b.token),Math.floor(Date.now()/1000)+1800).run();}catch{check(false,409,'This form was already submitted. Reload before another response.');}
  const id=random(16),receipt=random(24),now=new Date().toISOString();await env.DB.prepare('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?)').bind(id,await hash(receipt),rid,subject,message,nickname,b.consent_public?1:0,'','pending',now,now).run();
  return response({ok:true,id,receipt,message:'Received privately. Save your response key to read the reply. It cannot be recovered if lost.'},201,cors);
 }
 if(path==='/api/community/lookup'){
  await rate(env,request,'lookup',30);check(typeof b.id==='string'&&/^[a-f0-9]{32}$/.test(b.id)&&typeof b.receipt==='string'&&/^[a-f0-9]{48}$/.test(b.receipt),404,'Response key not found.');const p=await env.DB.prepare('SELECT * FROM messages WHERE id=?').bind(b.id).first();check(p&&await equal(p.receipt_hash,await hash(b.receipt)),404,'Response key not found.');delete p.receipt_hash;return response({item:p},200,cors);
 }
 check(false,404,'Response operation not found.');
 }catch(e){return response({error:e.status?e.message:'The response service is temporarily unavailable.'},e.status||503,cors);}}
export default {fetch:handle};
