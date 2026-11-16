// Called only by the annotated-tag GitHub Actions job. Never run locally.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
if(process.env.GITHUB_ACTIONS!=='true'||process.env.NEWS_DEPLOY_GATE!=='verified')throw Error('Actions release gate required');
const account='97608888ce434ffd0b3883a0e91396e1',name='nice-news-data-v1',token=process.env.NICE_NEWS_CLOUDFLARE_API_TOKEN;
if(!token)throw Error('missing publishing credential');
const root=`https://api.cloudflare.com/client/v4/accounts/${account}/workers/scripts/${name}`;
async function api(url,opts={}){const r=await fetch(url,{...opts,headers:{Authorization:`Bearer ${token}`,...opts.headers}});const x=await r.json();if(!r.ok||!x.success)throw Error(`Cloudflare ${r.status}: ${JSON.stringify(x.errors?.map(e=>({code:e.code,message:e.message})))}`);return x.result;}
function snapshot(x){return(x.bindings||[]).map(b=>({name:b.name,type:b.type,state:b.type==='secret_text'?'redacted':b.type==='plain_text'?(String(b.text||'').trim()?'nonempty':'empty'):'bound'})).sort((a,b)=>a.name.localeCompare(b.name));}
await fs.mkdir('news-service/release-evidence',{recursive:true});
const before=await api(root+'/settings');const snap=snapshot(before);
const expected=JSON.parse(await fs.readFile('news-service/expected-config.json','utf8'));
if(JSON.stringify(snap)!==JSON.stringify(expected.before))throw Error('configuration drift; no upload performed');
if(snap.some(b=>b.state==='empty'))throw Error('empty config binding');
if(snap.some(b=>!['NEWS','NEWS_PUBLISH_TOKEN_SHA256'].includes(b.name)))throw Error('unexpected binding; review before deployment');
await fs.writeFile('news-service/release-evidence/config-before.json',JSON.stringify(snap,null,2));
const metadata={main_module:'worker.mjs',compatibility_date:'2026-11-16',keep_bindings:['secret_text'],bindings:[{type:'r2_bucket',name:'NEWS',bucket_name:'nice-news-data-v1'},{type:'plain_text',name:'NEWS_PUBLISH_TOKEN_SHA256',text:crypto.createHash('sha256').update(token).digest('hex')}]};
const form=new FormData();form.append('metadata',JSON.stringify(metadata));
const hashes={};for(const f of ['worker.mjs','render.mjs']){const body=await fs.readFile('news-service/'+f);hashes[f]=crypto.createHash('sha256').update(body).digest('hex');form.append(f,new Blob([body],{type:'application/javascript+module'}),f);}
const result=await api(root,{method:'PUT',body:form});
const after=await api(root+'/settings'),afterSnap=snapshot(after);
await fs.writeFile('news-service/release-evidence/config-after.json',JSON.stringify(afterSnap,null,2));
if(JSON.stringify(afterSnap)!==JSON.stringify(expected.after)||after.bindings.find(b=>b.name==='NEWS')?.bucket_name!=='nice-news-data-v1'||after.bindings.find(b=>b.name==='NEWS_PUBLISH_TOKEN_SHA256')?.text!==metadata.bindings[1].text)throw Error('configuration mismatch; stop and rollback');
await fs.writeFile('news-service/release-evidence/deployment.json',JSON.stringify({id:result.id,deployment_id:result.deployment_id,version_id:result.version_id,hashes,account,name,secret_values:'not read; preservation checked by binding names'},null,2));
console.log('News Worker deployment completed; see release-evidence for ID and hashes.');
