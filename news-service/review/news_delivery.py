"""Exact-version delivery. Only existing approved outbox rows may be sent."""
import json,os,time,urllib.request,urllib.error,subprocess
from pathlib import Path
from news_data import digest,canonical,require
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

class Delivery:
 def __init__(self,store,transport=None):
  self.store=store;self.transport=transport or self.request
  with store.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS delivery_receipts(event_key TEXT PRIMARY KEY, body TEXT, received INTEGER)')
 def request(self,path,payload=None):
  token=os.environ.get('NICE_NEWS_PUBLISH_TOKEN','')
  if not token:
   try:
    p=subprocess.run(['/usr/bin/python3',str(Path(__file__).with_name('news_keychain_transport.py'))],input=canonical({'path':path,'payload':payload}),text=True,capture_output=True,timeout=20)
    require(p.returncode==0,'发布连接暂未确认');return json.loads(p.stdout)
   except Exception:raise RuntimeError('发布回执暂未确认，请稍后刷新核对') from None
  req=urllib.request.Request('https://nice-news-data-v1.gerheidicn.workers.dev'+path,data=canonical(payload).encode() if payload is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
  try:
   with urllib.request.build_opener(NoRedirect).open(req,timeout=15) as r:return json.load(r)
  except Exception:raise RuntimeError('发布回执暂未确认，请稍后刷新核对') from None
 def ready(self):
  try:return self.transport('/__news/status').get('ready') is True
  except Exception:return False
 def accept(self,row,receipt):
  expected='published' if row['action']=='approve' else 'withdrawn'
  require(isinstance(receipt,dict) and all(receipt.get(k)==row[k] for k in ('id','hash','action')) and receipt.get('event_key')==row['key'] and receipt.get('state')==expected,'发布回执版本不符')
  require(type(receipt.get('generation')) is int and receipt['generation']>0,'发布代数不符')
  with self.store.connect() as db:
   db.execute('BEGIN IMMEDIATE')
   current=db.execute('SELECT * FROM outbox WHERE key=?',(row['key'],)).fetchone()
   require(current and current['state'] in ('sending','sent'),'发布记录状态不符')
   if current['state']=='sent':
    prior=db.execute('SELECT body FROM delivery_receipts WHERE event_key=?',(row['key'],)).fetchone()
    require(prior and json.loads(prior[0])==receipt,'重复回执不一致')
    return receipt
   head=db.execute('SELECT * FROM heads WHERE id=?',(row['id'],)).fetchone()
   require(head and head['hash']==row['hash'],'本地版本变化，停止核对')
   db.execute('INSERT OR IGNORE INTO delivery_receipts VALUES(?,?,?)',(row['key'],canonical(receipt),int(time.time())))
   db.execute("UPDATE outbox SET state='sent' WHERE key=?",(row['key'],))
   db.execute('UPDATE heads SET state=? WHERE id=? AND hash=?',(expected,row['id'],row['hash']))
  return receipt
 def confirm(self,row):
  result=self.transport('/__news/status?event_key='+row['key'])
  receipt=result.get('receipt')
  if not receipt:return None
  expected=row['hash'] if row['action']=='approve' else None
  require(result.get('current_hash')==expected,'历史回执与当前上线版本不一致，请人工核对')
  return self.accept(row,receipt)
 def reconcile(self,ident):
  with self.store.connect() as db:rows=[dict(r) for r in db.execute("SELECT * FROM outbox WHERE id=? AND state='sending' ORDER BY created,key",(ident,))]
  for row in rows:
   self.confirm(row)
  return not any(self.pending(ident,'sending'))
 def pending(self,ident,state):
  with self.store.connect() as db:return [dict(r) for r in db.execute('SELECT * FROM outbox WHERE id=? AND state=?',(ident,state))]
 def deliver(self,ident):
  # Persist sending BEFORE network I/O: a timeout cannot be cancelled as unsent.
  with self.store.connect() as db:
   db.execute('BEGIN IMMEDIATE')
   rows=db.execute("SELECT * FROM outbox WHERE id=? AND state IN ('pending','sending') ORDER BY created,key",(ident,)).fetchall()
   if not rows:return None
   require(len(rows)==1,'待核对记录不唯一')
   row=dict(rows[0]);head=db.execute('SELECT * FROM heads WHERE id=?',(ident,)).fetchone()
   require(head and head['hash']==row['hash'] and head['state'] in ('approved_pending_publish','withdraw_pending'),'缺少当前已批准版本')
   approval=db.execute('SELECT 1 FROM decisions WHERE id=? AND hash=? AND action=?',(ident,row['hash'],row['action'])).fetchone()
   require(approval,'缺少审批记录')
   document=json.loads(db.execute('SELECT body FROM revisions WHERE id=? AND hash=?',(ident,row['hash'])).fetchone()[0])
   require(digest(document)==row['hash'],'固定版本被修改')
   db.execute("UPDATE outbox SET state='sending' WHERE key=?",(row['key'],))
  status=self.transport('/__news/status?event_key='+row['key'])
  if status.get('receipt'):return self.confirm(row)
  result=self.transport('/__news/publish',{'id':ident,'hash':row['hash'],'action':row['action'],'event_key':row['key'],'expected_generation':status['generation'],'document':document if row['action']=='approve' else None})
  require(result.get('event_key')==row['key'] and result.get('hash')==row['hash'],'发布回执版本不符')
  receipt=self.confirm(row);require(receipt,'尚未读到发布回执');return receipt
