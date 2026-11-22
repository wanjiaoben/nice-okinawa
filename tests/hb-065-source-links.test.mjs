import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const links = {
  reddit: ['reddit', 'utm_source=reddit'],
  linkedin: ['linkedin', 'utm_source=linkedin'],
  shorts: ['youtube_shorts', 'utm_source=youtube_shorts'],
  ig: ['instagram', 'utm_source=instagram'],
  'book-vocabulary': ['book_vocabulary_en', '/books/vocab-en/'],
  'book-lipbalm': ['book_lipbalm_en', '/mogi/trial/'],
  'book-coursebook': ['book_coursebook_en', '/mogi/trial/']
};

test('seven fixed short links use the shared aggregate-only redirect script', () => {
  for (const [slug, [source, marker]] of Object.entries(links)) {
    const html = fs.readFileSync(path.join(root, 'go', slug, 'index.html'), 'utf8');
    assert.match(html, new RegExp(`data-source="${source}"`));
    assert.ok(html.includes(marker));
    assert.match(html, /<meta name="robots" content="noindex,nofollow">/);
    assert.match(html, /<script src="\/go\/redirect\.js"><\/script>/);
  }
});

test('redirect script sends only the fixed source code and never reads personal identifiers', () => {
  const script = fs.readFileSync(path.join(root, 'go', 'redirect.js'), 'utf8');
  assert.match(script, /JSON\.stringify\(\{ source: source \}\)/);
  assert.doesNotMatch(script, /cookie|localStorage|sessionStorage|email|visitor|userAgent|referrer/i);
  assert.match(script, /location\.replace\(target\)/);
});
