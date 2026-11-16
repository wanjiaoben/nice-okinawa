import json,tempfile,time,unittest
from pathlib import Path
from news_data import Store,digest
from news_delivery import Delivery

class DeliveryTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=Store(self.tmp.name)
  self.d=json.loads((Path(__file__).parent.parent/'example.json').read_text())
  now=int(time.time());self.d['fact_check'].update(checked_at=now,valid_until=now+3600)
  self.row=self.s.enqueue(self.d);self.id=self.row['id'];self.h=self.row['hash'];self.calls=0;self.receipts={};self.generation=0;self.current=None
 def approve(self):self.s.decide(self.id,self.h,'approve','wan@example.test',self.s.token(self.id,'wan@example.test'),True)
 def transport(self,path,p=None):
  if p is None:return {'ready':True,'generation':self.generation,'receipt':self.receipts.get(path.split('event_key=')[-1]),'current_hash':self.current}
  self.calls+=1;self.generation+=1
  self.current=p['hash'] if p['action']=='approve' else None
  r={k:p[k] for k in ('id','hash','action','event_key')};r.update(generation=self.generation,state='published' if p['action']=='approve' else 'withdrawn');self.receipts[p['event_key']]=r;return r
 def test_no_approval_no_delivery(self):
  self.assertIsNone(Delivery(self.s,self.transport).deliver(self.id));self.assertEqual(self.calls,0)
 def test_publish_duplicate_and_withdraw(self):
  self.approve();d=Delivery(self.s,self.transport);d.deliver(self.id);d.deliver(self.id)
  self.assertEqual(self.calls,1);self.assertEqual(self.s.get(self.id)[0]['state'],'published')
  self.s.decide(self.id,self.h,'withdraw','wan@example.test',self.s.token(self.id,'wan@example.test'),True);d.deliver(self.id)
  self.assertEqual(self.calls,2);self.assertEqual(self.s.get(self.id)[0]['state'],'withdrawn')
 def test_remote_success_lost_response_reconciles(self):
  self.approve()
  def lost(path,p=None):
   result=self.transport(path,p)
   if p:raise TimeoutError('local fixture timeout')
   return result
  d=Delivery(self.s,lost)
  with self.assertRaises(TimeoutError):d.deliver(self.id)
  with self.assertRaises(ValueError):self.s.decide(self.id,self.h,'withdraw','wan@example.test',self.s.token(self.id,'wan@example.test'),True)
  self.assertTrue(d.reconcile(self.id));self.assertEqual(self.calls,1);self.assertEqual(self.s.get(self.id)[0]['state'],'published')
 def test_unknown_can_retry_same_approved_event(self):
  self.approve()
  def down(path,p=None):raise TimeoutError('offline fixture')
  with self.assertRaises(TimeoutError):Delivery(self.s,down).deliver(self.id)
  Delivery(self.s,self.transport).deliver(self.id);self.assertEqual(self.calls,1)
 def test_forged_receipt_does_not_mark_published(self):
  self.approve()
  def forged(path,p=None):
   r=self.transport(path,p)
   if p:r={**r,'hash':'0'*64}
   return r
  with self.assertRaises(ValueError):Delivery(self.s,forged).deliver(self.id)
  self.assertEqual(self.s.get(self.id)[0]['state'],'approved_pending_publish')
 def test_changed_content_refused(self):
  self.approve()
  with self.s.connect() as db:db.execute('UPDATE revisions SET body=?',(json.dumps({**self.d,'id':'CHANGED'}),))
  with self.assertRaises(ValueError):Delivery(self.s,self.transport).deliver(self.id)
  self.assertEqual(self.calls,0)
 def test_historical_receipt_not_current_publication(self):
  self.approve();d=Delivery(self.s,self.transport)
  def lost(path,p=None):
   r=self.transport(path,p)
   if p:raise TimeoutError('response lost')
   return r
  with self.assertRaises(TimeoutError):Delivery(self.s,lost).deliver(self.id)
  self.current=None
  with self.assertRaises(ValueError):d.reconcile(self.id)
  self.assertEqual(self.s.get(self.id)[0]['state'],'approved_pending_publish')
 def test_late_approve_receipt_preserves_withdrawn(self):
  self.approve();d=Delivery(self.s,self.transport)
  with self.s.connect() as db:row=dict(db.execute('SELECT * FROM outbox').fetchone())
  receipt=d.deliver(self.id)
  self.s.decide(self.id,self.h,'withdraw','wan@example.test',self.s.token(self.id,'wan@example.test'),True)
  d.deliver(self.id);d.accept(row,receipt)
  self.assertEqual(self.s.get(self.id)[0]['state'],'withdrawn')
 def test_retry_action_keeps_original_outbox(self):
  self.approve()
  def down(path,p=None):raise TimeoutError('offline fixture')
  with self.assertRaises(TimeoutError):Delivery(self.s,down).deliver(self.id)
  self.s.decide(self.id,self.h,'retry','wan@example.test',self.s.token(self.id,'wan@example.test'),True)
  with self.s.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM outbox').fetchone()[0],1)
  Delivery(self.s,self.transport).deliver(self.id);self.assertEqual(self.calls,1)
if __name__=='__main__':unittest.main()
