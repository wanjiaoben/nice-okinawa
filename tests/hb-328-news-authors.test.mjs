import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

function source(path) {
  return fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
}

function newsArticle(html) {
  const scripts = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
    .map((match) => JSON.parse(match[1]));
  const nodes = scripts.flatMap((entry) => entry['@graph'] || [entry]);
  return nodes.find((entry) => entry['@type'] === 'NewsArticle');
}

test('HB-328 travel news uses Nice Okinawa as the visible and structured author', () => {
  const slugs = [
    'naha-airport-rental-car-safety-20261106',
    'onna-minami-bypass-partial-four-lanes-20261121',
    'naha-shurijo-reconstruction-support-grant-2026',
    'shurijo-seiden-public-opening-20261123',
  ];
  for (const locale of ['en', 'ja', 'zh-hans', 'zh-hant']) {
    for (const slug of slugs) {
      const html = source(`${locale}/news/${slug}/index.html`);
      assert.equal(newsArticle(html)?.author?.name, 'Nice Okinawa');
      assert.match(html, /[·｜] Nice Okinawa<\/p>/);
    }
  }
  for (const locale of ['en', 'ja', 'zh-hant']) {
    const html = source(`${locale}/news/okinawa-tourism-h1-2026/index.html`);
    assert.equal(newsArticle(html)?.author?.name, 'Nice Okinawa');
    assert.doesNotMatch(html, /Nice Okinawa \/ Catalina Japan/);
  }
  for (const locale of ['en', 'ja', 'zh-hans']) {
    assert.match(source(`${locale}/news/okinawa-licensed-transport-guide-20261104/index.html`), /2026-11-04 · Nice Okinawa/);
  }
});

test('HB-328 learning news uses the language-specific Shinko Lab author', () => {
  const expected = { en: 'Shinko Lab', ja: '深耕ラボ', 'zh-hans': '深耕自留地研究室', 'zh-hant': '深耕自留地研究室' };
  for (const [locale, author] of Object.entries(expected)) {
    const html = source(`${locale}/news/highly-skilled-j-find-university-list-2026-10/index.html`);
    assert.equal(newsArticle(html)?.author?.name, author);
    assert.match(html, new RegExp(`${author.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}</p>`));
  }
});
