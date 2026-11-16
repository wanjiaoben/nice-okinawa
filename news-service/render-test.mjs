import fs from'node:fs/promises';import assert from'node:assert/strict';import {languages,renderArticle,renderList,publicIndex,sitemap,validatePublic}from'./render.mjs';
const doc=JSON.parse(await fs.readFile(new URL('./example.json',import.meta.url),'utf8'));let checks=0;
for(const lang of languages){const a=renderArticle(doc,lang);assert(a.includes(doc.languages[lang].title));assert(a.includes('hreflang="'+lang+'"'));assert(a.includes('mailto:info@nice.okinawa'));assert(!a.includes('<script'));assert(renderList([doc],lang).includes('/'+doc.id+'/'));assert(renderList([],lang).includes('<h1>'));checks+=6;}
assert.equal(publicIndex([doc]).items.length,1);assert.equal((sitemap([doc]).match(/<url>/g)||[]).length,4);checks+=2;
for(const mutate of [d=>d.languages.en.byline='CATALINA JAPAN',d=>delete d.languages.ja,d=>d.sources=['javascript:alert(1)'],d=>d.id='../admin']){const d=structuredClone(doc);mutate(d);assert.throws(()=>validatePublic(d));checks++;}
const x=structuredClone(doc);x.languages.en.body='<img src=x onerror=alert(1)>';assert(renderArticle(x,'en').includes('&lt;img'));checks++;
const result={passed:true,checks,scope:'local renderer only, fixture not approved or published; no storage writer installed'};console.log(result);
