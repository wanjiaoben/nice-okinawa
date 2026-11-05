const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const base=process.env.HOME_PREVIEW_URL||'http://127.0.0.1:8912/';
const evidence=process.env.HOME_EVIDENCE_DIR||'/tmp/nice-compact-evidence';
const expected=['activity','snorkel','fishing','golf','rental','kiso','bjt','progress','training','japanusedcars','translation'];
(async()=>{const browser=await chromium.launch();const rows=[];try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 await page.route('**/analytics.nice.okinawa/**',r=>r.abort());
 await page.goto(base+'?lang=zh-Hans');
 const entries=await page.locator('.business-entry').evaluateAll(nodes=>nodes.map(n=>({service:n.dataset.business,url:n.href})));
 assert.deepEqual(entries.map(e=>e.service),expected);
 for(const e of entries) assert.equal(e.url,`https://${e.service}.nice.okinawa/`);
 assert.equal(await page.locator('.hero img').count(),0);
 assert((await page.locator('.hero').boundingBox()).height<520,'Desktop intro should be compact');
 // Follow the actual customer link; no forms, credentials, or business actions.
 for(const e of entries){
  await page.goto(base+'?lang=zh-Hans');
  try{
   const response=await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded',timeout:25000}),page.locator(`[data-business="${e.service}"]`).click()]).then(x=>x[0]);
   rows.push({...e,status:response?.status(),final_url:page.url(),title:await page.title()});
  }catch(error){rows.push({...e,final_url:page.url(),error:error.message.split('\n')[0]});}
 }
 fs.mkdirSync(evidence,{recursive:true});fs.writeFileSync(evidence+'/destination-clicks.json',JSON.stringify(rows,null,2));
 console.log(JSON.stringify(rows,null,2));
 assert(rows.every(e=>e.status===200&&new URL(e.final_url).hostname===new URL(e.url).hostname),'Some live destinations need follow-up; see evidence');
 console.log('PASS all 11 actual business-entry clicks reached their matching live homepage with HTTP 200.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
