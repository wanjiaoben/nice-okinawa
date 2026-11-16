import {languages,validatePublic,renderArticle,renderList,publicIndex,sitemap} from './render.mjs';
const enc=new TextEncoder();
export const canonical=x=>JSON.stringify(x instanceof Array?x.map(normalize):normalize(x));
function normalize(x){return x&&typeof x==='object'?(Array.isArray(x)?x.map(normalize):Object.fromEntries(Object.keys(x).sort().map(k=>[k,normalize(x[k])]))):x;}
export async function digest(x){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(typeof x==='string'?x:canonical(x))))).map(b=>b.toString(16).padStart(2,'0')).join('');}
const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin'};
function json(x,status=200){return new Response(JSON.stringify(x),{status,headers:{...headers,'Content-Type':'application/json; charset=utf-8'}});}
function page(body,type='text/html; charset=utf-8',status=200){return new Response(body,{status,headers:{...headers,'Content-Type':type,'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"}});}
function check(ok,msg){if(!ok)throw Error(msg);}
function document(d,now){
 validatePublic(d);check(Object.keys(d).sort().join(',')==='category,fact_check,id,languages,schema,sources','document_fields');
 check(/^[A-Z][A-Z0-9-]{2,79}$/.test(d.id),'document_id');
 check(Object.keys(d.languages).sort().join(',')===[...languages].sort().join(','),'languages');
 for(const x of Object.values(d.languages)){
  check(Object.keys(x).sort().join(',')==='body,byline,summary,title','language_fields');
  for(const [k,n] of [['title',180],['summary',500],['body',50000],['byline',100]])check(x[k].length<=n&&!/[\0]|<\s*\/?\s*[a-z!]|javascript:|data:text\/html/i.test(x[k]),'unsafe_text');
 }
 const f=d.fact_check;check(f&&Object.keys(f).sort().join(',')==='checked_at,note,valid_until','fact_check');
 check(Number.isInteger(f.checked_at)&&Number.isInteger(f.valid_until)&&f.checked_at<=now+60&&f.valid_until>now+60&&f.valid_until-f.checked_at<=604800&&f.valid_until>=f.checked_at,'fact_check_expired');
 check(typeof f.note==='string'&&f.note.length>=10&&f.note.length<=3000,'fact_note');
 check(d.sources.length<=30&&d.sources.every(x=>x.length<2048&&!new URL(x).hash),'sources');
 check(enc.encode(canonical(d)).length<=500000,'document_size');
}
async function state(bucket){const o=await bucket.get('news-v1/head.json');if(!o)return {etag:null,value:{generation:0,articles:{},receipts:{}}};return{etag:o.etag,value:await o.json()};}
async function authenticated(req,env){
 if(!/^[a-f0-9]{64}$/.test(env.NEWS_PUBLISH_TOKEN_SHA256||''))return false;
 const v=req.headers.get('Authorization')||'';if(!v.startsWith('Bearer ')||v.length>512)return false;
 const actual=await digest(v.slice(7));let diff=0;for(let i=0;i<64;i++)diff|=actual.charCodeAt(i)^env.NEWS_PUBLISH_TOKEN_SHA256.charCodeAt(i);return diff===0;
}
async function write(req,env){
 if(!await authenticated(req,env))return json({error:'unauthorized'},403);
 if(req.headers.get('content-type')!=='application/json')return json({error:'content_type'},415);
 const raw=await req.text();if(enc.encode(raw).length>510000)return json({error:'too_large'},413);
 let p;try{p=JSON.parse(raw);check(Object.keys(p).sort().join(',')==='action,document,event_key,expected_generation,hash,id','request_fields');check(['approve','withdraw'].includes(p.action),'action');check(Number.isSafeInteger(p.expected_generation)&&p.expected_generation>=0,'generation');check(/^[a-f0-9]{64}$/.test(p.hash),'hash');check(p.event_key===await digest([p.id,p.hash,p.action]),'event_key');if(p.action==='approve'){document(p.document,Date.now()/1000);check(p.document.id===p.id&&await digest(p.document)===p.hash,'exact_version');}else check(p.document===null,'withdraw_document');}catch(e){return json({error:e.message},400);}
 const old=await state(env.NEWS);if(old.value.receipts[p.event_key])return json(old.value.receipts[p.event_key]);
 if(old.value.generation!==p.expected_generation)return json({error:'generation_conflict',generation:old.value.generation},409);
 const current=old.value.articles[p.id];
 if(p.action==='withdraw'&&(!current||current.hash!==p.hash))return json({error:'version_conflict'},409);
 if(p.action==='approve'&&current&&current.hash!==p.hash)return json({error:'withdraw_before_replace'},409);
 // Revisions are immutable and never deleted. One conditional head write atomically
 // switches all four languages, index, sitemap and the idempotency receipt.
 if(p.action==='approve')await env.NEWS.put('news-v1/revisions/'+p.id+'/'+p.hash+'.json',canonical(p.document),{onlyIf:{etagDoesNotMatch:'*'},httpMetadata:{contentType:'application/json'}});
 const receipt={id:p.id,hash:p.hash,event_key:p.event_key,action:p.action,generation:old.value.generation+1,state:p.action==='approve'?'published':'withdrawn',at:new Date().toISOString()};
 const next=structuredClone(old.value);next.generation=receipt.generation;next.receipts[p.event_key]=receipt;
 if(p.action==='approve')next.articles[p.id]={hash:p.hash,document:p.document};else delete next.articles[p.id];
 if(Object.keys(next.articles).length>1000||enc.encode(canonical(next)).length>10000000)return json({error:'capacity_requires_review'},409);
 const saved=await env.NEWS.put('news-v1/head.json',canonical(next),{onlyIf:old.etag?{etagMatches:old.etag}:{etagDoesNotMatch:'*'},httpMetadata:{contentType:'application/json'}});
 return saved?json(receipt):json({error:'generation_conflict'},409);
}
export default {async fetch(req,env){
 const u=new URL(req.url),p=u.pathname;
 if(!env.NEWS)return json({error:'storage_not_ready'},503);
 try{
  if(p==='/__news/publish')return req.method==='POST'?await write(req,env):json({error:'method'},405);
  if(p==='/__news/status'){
   if(!await authenticated(req,env))return json({error:'unauthorized'},403);
   const s=await state(env.NEWS),key=u.searchParams.get('event_key'),receipt=key?s.value.receipts[key]:null;return json(key?{receipt:receipt||null,generation:s.value.generation,current_hash:receipt?(s.value.articles[receipt.id]?.hash||null):null}:{generation:s.value.generation,ready:true});
  }
  if(!['GET','HEAD'].includes(req.method))return json({error:'method'},405);
  const s=await state(env.NEWS),docs=Object.values(s.value.articles).map(x=>x.document);
  if(p==='/api/news/v1/index.json')return json({...publicIndex(docs),generation:s.value.generation});
  if(p==='/news-sitemap.xml')return page(sitemap(docs),'application/xml; charset=utf-8');
  const m=/^\/newsroom\/(en|zh-Hant|ja|zh-Hans)\/(?:([A-Z][A-Z0-9-]{2,79})\/)?$/.exec(p);
  if(m){if(!m[2])return page(renderList(docs,m[1]));const a=s.value.articles[m[2]];return a?page(renderArticle(a.document,m[1])):page('Not found','text/plain',404);}
  return page('Not found','text/plain',404);
 }catch{return json({error:'news_unavailable'},503);}
}};
