"""HB-149 bilingual fixed-copy publication contract; no network or credentials."""
from pathlib import Path
import json,re,unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
SLUGS=['','car-rental','travel-agencies','chauffeur','activities','mice','shore-excursions','guides-interpreters','business-interpreting']
class B2B(unittest.TestCase):
 def test_pages(self):
  for lang in ['zh-hans','en']:
   for slug in SLUGS:
    route=f'/{lang}/partners/'+(slug+'/' if slug else '')
    with self.subTest(route=route):
     s=(ROOT/route.lstrip('/')/'index.html').read_text()
     self.assertIn(f'<link rel="canonical" href="https://nice.okinawa{route}"',s)
     self.assertNotIn('noindex',s)
     self.assertEqual(len(re.findall(r'<h1[ >]',s)),1)
     for other,tag in [('zh-hans','zh-Hans'),('en','en')]:
      self.assertRegex(s,rf'hreflang="{tag}"[^>]+href="https://nice.okinawa/{other}/partners/')
     blocks=re.findall(r'<script type="application/ld\+json">(.*?)</script>',s,re.S)
     self.assertEqual(len(blocks),1)
     g=json.loads(blocks[0]);self.assertNotIn('telephone',json.dumps(g))
     faq=next(x for x in g['@graph'] if x['@type']=='FAQPage')
     self.assertEqual(len(faq['mainEntity']),9)
     for q in faq['mainEntity']:
      self.assertTrue(q['name']);self.assertTrue(q['acceptedAnswer']['text'])
     self.assertIn('mailto:info@nice.okinawa',s);self.assertIn('https://wa.me/817089523968',s)
     for href in re.findall(r'href="(/[^"#?]*)"',s):
      self.assertTrue((ROOT/href.lstrip('/')/'index.html').exists(),href)
 def test_index_entries(self):
  urls=[x.text for x in ET.parse(ROOT/'sitemap.xml').iter() if x.tag.endswith('}loc')]
  for lang in ['zh-hans','en']:
   for slug in SLUGS:self.assertEqual(urls.count(f'https://nice.okinawa/{lang}/partners/'+(slug+'/' if slug else '')),1)
   self.assertIn(f'/{lang}/partners/',(ROOT/lang/'kerama-snorkeling/index.html').read_text())
  self.assertIn('b2bDesk',(ROOT/'content/home/copy.json').read_text())
if __name__=='__main__':unittest.main()
