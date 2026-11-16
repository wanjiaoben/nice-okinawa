import sys,json,tempfile,time,copy,unittest,types,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from news_data import *
from news_data_review import App,demo,mount
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name);self.doc=demo();self.doc['id']='TEST-ARTICLE';self.actor='wan@example.invalid';self.row=self.store.enqueue(self.doc)
 def tearDown(self):self.tmp.cleanup()
 def approve(self):return self.store.decide(self.doc['id'],self.row['hash'],'approve',self.actor,self.store.token(self.doc['id'],self.actor),True)
 def test_exact_four_languages(self):self.assertEqual(set(validate(self.doc)['languages']),set(LANGS))
 def test_missing_language(self):
  d=copy.deepcopy(self.doc);del d['languages']['ja']
  with self.assertRaises(ValueError):validate(d)
 def test_company_byline_rejected(self):
  d=copy.deepcopy(self.doc);d['languages']['en']['byline']='CATALINA JAPAN'
  with self.assertRaises(ValueError):validate(d)
 def test_company_body_rejected(self):
  d=copy.deepcopy(self.doc);d['languages']['ja']['body']='CATALINA JAPAN'
  with self.assertRaises(ValueError):validate(d)
 def test_html_rejected(self):
  d=copy.deepcopy(self.doc);d['languages']['en']['body']='<img onerror=alert(1)>'
  with self.assertRaises(ValueError):validate(d)
 def test_url_credentials_rejected(self):
  d=copy.deepcopy(self.doc);d['sources']=['https://name:secret@example.invalid/']
  with self.assertRaises(ValueError):validate(d)
 def test_empty_sources_rejected(self):
  d=copy.deepcopy(self.doc);d['sources']=[]
  with self.assertRaises(ValueError):validate(d)
 def test_stale_revision_rejected(self):
  with self.assertRaises(ValueError):self.store.decide(self.doc['id'],'0'*64,'approve',self.actor,self.store.token(self.doc['id'],self.actor),True)
 def test_no_delivery_no_approval(self):
  with self.assertRaises(ValueError):self.store.decide(self.doc['id'],self.row['hash'],'approve',self.actor,self.store.token(self.doc['id'],self.actor),False)
  self.assertEqual(self.store.get(self.doc['id'])[0]['state'],'pending_review')
 def test_wrong_actor_token(self):
  with self.assertRaises(ValueError):self.store.decide(self.doc['id'],self.row['hash'],'approve','other@example.invalid',self.store.token(self.doc['id'],self.actor),True)
 def test_missing_token(self):
  with self.assertRaises(ValueError):self.store.decide(self.doc['id'],self.row['hash'],'approve',self.actor,'invalid',True)
 def test_expired_token(self):
  t=self.store.token(self.doc['id'],self.actor)
  with self.store.connect() as db:db.execute('UPDATE tokens SET expires=0')
  with self.assertRaises(ValueError):self.store.decide(self.doc['id'],self.row['hash'],'approve',self.actor,t,True)
 def test_approve_exact_and_no_duplicate(self):
  self.assertEqual(self.approve()['state'],'approved_pending_publish')
  with self.assertRaises(ValueError):self.approve()
  with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM outbox').fetchone()[0],1)
 def test_reject_and_revise(self):
  self.store.decide(self.doc['id'],self.row['hash'],'reject',self.actor,self.store.token(self.doc['id'],self.actor))
  d=copy.deepcopy(self.doc);d['languages']['en']['body']+=' A revision.';r=self.store.enqueue(d,self.row['hash']);self.assertNotEqual(r['hash'],self.row['hash'])
 def test_approved_cannot_replace(self):
  self.approve();d=copy.deepcopy(self.doc);d['languages']['en']['body']+=' Changed.'
  with self.assertRaises(ValueError):self.store.enqueue(d,self.row['hash'])
 def test_withdraw_pending_cancels_outbox(self):
  self.approve();r=self.store.decide(self.doc['id'],self.row['hash'],'withdraw',self.actor,self.store.token(self.doc['id'],self.actor));self.assertEqual(r['state'],'withdrawn')
  with self.store.connect() as db:self.assertEqual(db.execute('SELECT state FROM outbox').fetchone()[0],'cancelled');self.assertEqual(db.execute('SELECT count(*) FROM decisions').fetchone()[0],2)
 def test_published_withdraw_needs_transport(self):
  self.approve()
  with self.store.connect() as db:db.execute("UPDATE heads SET state='published'")
  with self.assertRaises(ValueError):self.store.decide(self.doc['id'],self.row['hash'],'withdraw',self.actor,self.store.token(self.doc['id'],self.actor),False)
  r=self.store.decide(self.doc['id'],self.row['hash'],'withdraw',self.actor,self.store.token(self.doc['id'],self.actor),True);self.assertEqual(r['state'],'withdraw_pending')
 def test_tamper_closed(self):
  with self.store.connect() as db:db.execute('UPDATE revisions SET body=?',(canonical({**self.doc,'category':'travel'}),))
  with self.assertRaises(ValueError):self.store.get(self.doc['id'])
 def test_expired_factcheck(self):
  d=copy.deepcopy(self.doc);d['fact_check'].update(checked_at=1,valid_until=3601);r=self.store.enqueue(d,self.row['hash'])
  with self.assertRaises(ValueError):self.store.decide(d['id'],r['hash'],'approve',self.actor,self.store.token(d['id'],self.actor),True)
 def test_nonce_invalidated_on_revision(self):
  t=self.store.token(self.doc['id'],self.actor);d=copy.deepcopy(self.doc);d['languages']['en']['body']+=' revised';r=self.store.enqueue(d,self.row['hash'])
  with self.assertRaises(ValueError):self.store.decide(d['id'],r['hash'],'approve',self.actor,t,True)
 def test_enqueue_idempotent(self):self.assertEqual(self.store.enqueue(self.doc)['hash'],self.row['hash'])
 def test_fixed_preview_matches_all_text(self):
  text=render(self.doc)
  for lang in LANGS:self.assertIn(html.escape(self.doc['languages'][lang]['body']),text);self.assertIn(BYLINES[lang],text)
 def test_existing_access_and_origin(self):
  s=types.SimpleNamespace(__file__=str(Path(self.tmp.name)/'review_server.py'),validate_origin=lambda h:None,access_identity=lambda h:{'email':self.actor} if h.get('jwt')=='verified' else {})
  app=App(s)
  with self.assertRaises(ValueError):app.identity({})
  with self.assertRaises(PermissionError):app.identity({'jwt':'verified','Origin':'https://evil.invalid'},True)
  self.assertEqual(app.identity({'jwt':'verified','Origin':'https://review.nice.okinawa'},True),self.actor);self.assertFalse(app.ready())
 def test_prod_never_test_bypass(self):
  s=types.SimpleNamespace(__file__=str(Path(self.tmp.name)/'review_server.py'),validate_origin=lambda h:None,access_identity=lambda h:{'email':self.actor});app=App(s);old=os.environ.get('REVIEW_TRUST_TEST_ACCESS');os.environ['REVIEW_TRUST_TEST_ACCESS']='1'
  try:
   with self.assertRaises(PermissionError):app.identity({})
  finally:
   if old is None:os.environ.pop('REVIEW_TRUST_TEST_ACCESS',None)
   else:os.environ['REVIEW_TRUST_TEST_ACCESS']=old
if __name__=='__main__':unittest.main(verbosity=2)
