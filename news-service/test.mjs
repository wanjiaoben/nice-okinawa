import assert from 'node:assert/strict';
import fs from 'node:fs';
import worker,{digest,canonical} from './worker.mjs';
class Bucket{
 constructor(){this.items=new Map();this.n=0;this.fail=false;}
 async get(k){const o=this.items.get(k);return o?{etag:o.etag,json:async()=>JSON.parse(o.body)}:null;}
 async put(k,body,opts={}){if(this.fail)throw Error('storage failed');const old=this.items.get(k),c=opts.onlyIf;if(c?.etagMatches&&old?.etag!==c.etagMatches||c?.etagDoesNotMatch==='*'&&old)return null;const o={etag:String(++this.n),body};this.items.set(k,o);return o;}
}
const token='fixture-only-not-a-credential';const env={NEWS:new Bucket(),NEWS_PUBLISH_TOKEN_SHA256:await digest(token)};
const base=JSON.parse(fs.readFileSync(new URL('./example.json',import.meta.url)));base.fact_check={checked_at:Math.floor(Date.now()/1000),valid_until:Math.floor(Date.now()/1000)+3600,note:'Local fixture only; never sent to production.'};
const hash=await digest(base),key=await digest([base.id,hash,'approve']);
const payload={id:base.id,document:base,hash,event_key:key,action:'approve',expected_generation:0};
let n=0;function eq(a,b){assert.deepEqual(a,b);n++;}
async function call(path,body,auth=token){return worker.fetch(new Request('https://nice.okinawa'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json',Authorization:'Bearer '+auth}:{Authorization:'Bearer '+auth},body:body?JSON.stringify(body):undefined}),env);}
eq((await call('/__news/publish',payload,'wrong')).status,403);
eq((await call('/__news/publish',{...payload,hash:'0'.repeat(64)})).status,400);
eq((await call('/__news/publish',{...payload,extra:1})).status,400);
eq((await call('/__news/status',null,'')).status,403);
const expired=structuredClone(payload);expired.document.fact_check.valid_until=1;expired.hash=await digest(expired.document);expired.event_key=await digest([expired.id,expired.hash,'approve']);eq((await call('/__news/publish',expired)).status,400);
const r=await call('/__news/publish',payload);eq(r.status,200);const receipt=await r.json();eq(receipt.generation,1);
eq(await (await call('/__news/publish',payload)).json(),receipt);
for(const lang of ['en','ja','zh-Hans','zh-Hant']){
 const a=await call('/newsroom/'+lang+'/'+base.id+'/');eq(a.status,200);assert((await a.text()).includes(base.languages[lang].title));n++;
 eq((await call('/newsroom/'+lang+'/')).status,200);
}
const index=await (await call('/api/news/v1/index.json')).json();eq(index.items.length,1);assert(!JSON.stringify(index).includes('fact_check'));n++;
eq(((await(await call('/news-sitemap.xml')).text()).match(/<url>/g)||[]).length,4);
eq((await call('/admin')).status,404);
const withdrawn={id:base.id,hash,event_key:await digest([base.id,hash,'withdraw']),action:'withdraw',document:null,expected_generation:1};
eq((await call('/__news/publish',{...withdrawn,expected_generation:0})).status,409);
eq((await call('/__news/publish',withdrawn)).status,200);eq((await call('/__news/publish',withdrawn)).status,200);
eq((await call('/newsroom/en/'+base.id+'/')).status,404);eq((await(await call('/api/news/v1/index.json')).json()).items.length,0);
assert(await env.NEWS.get('news-v1/revisions/'+base.id+'/'+hash+'.json'));n++;
env.NEWS.fail=true;const other=structuredClone(payload);other.id=other.document.id='SECOND-ARTICLE';other.hash=await digest(other.document);other.event_key=await digest([other.id,other.hash,'approve']);other.expected_generation=2;eq((await call('/__news/publish',other)).status,503);env.NEWS.fail=false;
eq((await(await call('/__news/status?event_key='+other.event_key)).json()).receipt,null);
// Two simultaneous changes to one generation cannot lose one another silently.
const alt=structuredClone(other);alt.id=alt.document.id='THIRD-ARTICLE';alt.hash=await digest(alt.document);alt.event_key=await digest([alt.id,alt.hash,'approve']);
eq((await Promise.all([call('/__news/publish',other),call('/__news/publish',alt)])).map(x=>x.status).sort(),[200,409]);
eq((await(await call('/api/news/v1/index.json')).json()).items.length,1);
eq(canonical({z:1,a:'汉字'}),'{"a":"汉字","z":1}');
console.log(JSON.stringify({passed:n,scope:'local fake R2; no real approval or publication'}));
