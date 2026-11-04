const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const palettes=require('../content/home/brand-palettes.json').palettes;
assert.equal(Object.keys(palettes).length,8);
assert(Object.values(palettes).every(row=>row.length===4));
const evidence=process.env.HOME_EVIDENCE_DIR||'/tmp/nice-home-reference-evidence';
fs.mkdirSync(evidence,{recursive:true});
const base=process.env.HOME_PREVIEW_URL||'http://127.0.0.1:8912/';
function luminance(hex){const rgb=hex.match(/[a-f\d]{2}/gi).map(x=>parseInt(x,16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722}
function ratio(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
assert(ratio('#00767C','#FFFFFF')>=4.5);
assert(ratio('#126482','#FFFFFF')>=4.5);
for(const colors of Object.values(palettes)) assert(ratio('#183E39',colors[3])>=4.5);
(async()=>{const browser=await chromium.launch();try{
let count=0;
for(const width of [320,390,768,1440]) for(const locale of ['zh-Hans','zh-Hant','ja','en']){
 const page=await browser.newPage({viewport:{width,height:1000},locale});
 await page.route('**/analytics.nice.okinawa/**',r=>r.abort());
 await page.goto(base+'?lang='+locale);
 const spec=await page.evaluate(()=>({bg:getComputedStyle(document.body).backgroundColor,learn:getComputedStyle(document.querySelector('#learn')).backgroundColor,travel:getComputedStyle(document.querySelector('#travel')).backgroundColor,radius:getComputedStyle(document.querySelector('.card')).borderRadius,button:document.querySelector('.button').getBoundingClientRect().height,columns:getComputedStyle(document.querySelector('.gateway')).gridTemplateColumns.split(' ').length,font:getComputedStyle(document.querySelector('h1')).fontFamily}));
 assert.equal(spec.bg,'rgb(255, 255, 255)');assert.equal(spec.learn,'rgb(244, 249, 235)');assert.equal(spec.travel,'rgb(239, 246, 250)');assert.equal(spec.radius,'14px');assert(spec.button>=52);assert(!/Georgia|Songti/.test(spec.font));
 if(width<700) assert.equal(spec.columns,1);
 await page.keyboard.press('Tab');assert(await page.locator(':focus-visible').count());
 await page.evaluate(()=>document.documentElement.style.fontSize='200%');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width}/${locale} at 200%`);
 for(const sel of ['#language','#submitBtn','#waBtn']) assert(await page.locator(sel).isVisible());
 if(locale==='zh-Hans'&&[390,1440].includes(width)) await page.screenshot({path:evidence+`/200pct-${width}.png`,fullPage:true});
 await page.close();count++;
}console.log(`PASS PDF alignment: ${count} viewport/language cases at 200% text; white hub, Main green, sea blue, single-column mobile, 14px cards, 52px controls, language fonts, keyboard focus; 32 palette values and text contrast.`);
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
