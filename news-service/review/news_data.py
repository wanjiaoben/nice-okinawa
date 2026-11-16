"""HB-174 data-only news contract and durable review journal. No auto-publisher."""
import argparse,contextlib,hashlib,html,json,os,re,secrets,sqlite3,time
from pathlib import Path
from urllib.parse import urlparse
LANGS=('zh-Hans','zh-Hant','en','ja')
BYLINES={'zh-Hans':'深耕自留地研究室','zh-Hant':'深耕自留地研究室','en':'Shinko Lab','ja':'深耕ラボ'}
def require(ok,message):
 if not ok:raise ValueError(message)
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def validate(d):
 require(isinstance(d,dict) and set(d)=={'schema','id','category','languages','sources','fact_check'},'稿件字段不完整或包含额外字段')
 require(d['schema']=='news-data-v1','稿件格式版本错误')
 require(isinstance(d['id'],str) and re.fullmatch(r'[A-Z][A-Z0-9-]{2,79}',d['id']),'稿件编号错误')
 require(d['category'] in ('learning','business','travel'),'类别错误')
 require(isinstance(d['languages'],dict) and set(d['languages'])==set(LANGS),'必须提供四语')
 for lang,v in d['languages'].items():
  require(isinstance(v,dict) and set(v)=={'title','summary','body','byline'},'四语稿件字段错误')
  for field,limit in [('title',180),('summary',500),('body',50000),('byline',100)]:
   t=v[field];require(isinstance(t,str) and bool(t.strip()) and len(t)<=limit and '\x00' not in t,'内容为空或过长')
   require(not re.search(r'<\s*/?\s*[a-z!]|javascript:|data:text/html',t,re.I),'正文只接收文字，不接收HTML或脚本')
  if d['category']=='learning':
   require(v['byline']==BYLINES[lang],'学习类署名不符')
   require(not re.search(r'catalina\s*japan|カタリナ|CATALINA',canonical(v),re.I),'学习类稿件不能使用公司名')
 require(isinstance(d['sources'],list) and 1<=len(d['sources'])<=30,'必须附来源链接')
 for u in d['sources']:
  require(isinstance(u,str) and len(u)<2048,'来源链接错误');p=urlparse(u)
  require(p.scheme=='https' and p.hostname and not p.username and not p.password and not p.fragment,'来源必须为无凭证HTTPS链接')
 f=d['fact_check'];require(isinstance(f,dict) and set(f)=={'checked_at','valid_until','note'},'必须提供事实核查记录')
 require(type(f['checked_at']) is int and type(f['valid_until']) is int and f['checked_at']<=f['valid_until'] and f['valid_until']-f['checked_at']<=7*86400,'事实核查期限错误')
 require(isinstance(f['note'],str) and 10<=len(f['note'])<=3000,'请说明摘要改写与来源核查')
 require(len(canonical(d).encode())<=500000,'稿件过大');return d
class Store:
 def __init__(self,root):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);os.chmod(self.root,0o700);self.path=self.root/'journal.sqlite'
  with self.connect() as db:db.executescript('''CREATE TABLE IF NOT EXISTS revisions(id TEXT,hash TEXT,body TEXT,created INTEGER,PRIMARY KEY(id,hash));CREATE TABLE IF NOT EXISTS heads(id TEXT PRIMARY KEY,hash TEXT,state TEXT);CREATE TABLE IF NOT EXISTS decisions(seq INTEGER PRIMARY KEY, id TEXT,hash TEXT,action TEXT,actor TEXT,at INTEGER);CREATE TABLE IF NOT EXISTS tokens(token TEXT PRIMARY KEY,id TEXT,hash TEXT,actor TEXT,expires INTEGER);CREATE TABLE IF NOT EXISTS outbox(key TEXT PRIMARY KEY,id TEXT,hash TEXT,action TEXT,state TEXT,created INTEGER);''')
  os.chmod(self.path,0o600)
 @contextlib.contextmanager
 def connect(self):
  db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row
  try:yield db;db.commit()
  except:db.rollback();raise
  finally:db.close()
 def enqueue(self,d,expected=None):
  validate(d);h=digest(d);now=int(time.time())
  with self.connect() as db:
   db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT * FROM heads WHERE id=?',(d['id'],)).fetchone()
   if old and old['hash']==h:return dict(old)
   require((old['hash'] if old else None)==expected,'稿件已变化，请重新读取版本')
   require(not old or old['state'] in ('pending_review','rejected','withdrawn'),'已批准稿件不得换版')
   db.execute('INSERT OR IGNORE INTO revisions VALUES(?,?,?,?)',(d['id'],h,canonical(d),now));db.execute('INSERT OR REPLACE INTO heads VALUES(?,?,?)',(d['id'],h,'pending_review'))
   db.execute('DELETE FROM tokens WHERE id=?',(d['id'],))
  return {'id':d['id'],'hash':h,'state':'pending_review'}
 def get(self,ident):
  with self.connect() as db:
   row=db.execute('SELECT h.*,r.body FROM heads h JOIN revisions r USING(id,hash) WHERE h.id=?',(ident,)).fetchone()
   require(row is not None,'稿件不存在');result=dict(row);doc=validate(json.loads(result.pop('body')));require(digest(doc)==result['hash'],'固定版本内容被修改');return result,doc
 def listing(self):
  with self.connect() as db:return [dict(r) for r in db.execute('SELECT * FROM heads ORDER BY id DESC')]
 def token(self,ident,actor):
  row,_=self.get(ident);token=secrets.token_urlsafe(32)
  with self.connect() as db:
   db.execute('DELETE FROM tokens WHERE expires<?',(int(time.time()),));db.execute('INSERT INTO tokens VALUES(?,?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),ident,row['hash'],actor,int(time.time())+1800))
  return token
 def decide(self,ident,h,action,actor,token,delivery_ready=False):
  require(action in ('approve','reject','withdraw','retry'),'不支持的操作');require(isinstance(actor,str) and '@' in actor,'缺少已验证身份')
  with self.connect() as db:
   db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM heads WHERE id=?',(ident,)).fetchone();require(row and row['hash']==h,'稿件版本已变化')
   raw=db.execute('SELECT body FROM revisions WHERE id=? AND hash=?',(ident,h)).fetchone();doc=validate(json.loads(raw[0]));require(digest(doc)==h,'固定内容被修改')
   token_hash=hashlib.sha256(token.encode()).hexdigest();t=db.execute('SELECT * FROM tokens WHERE token=?',(token_hash,)).fetchone();require(t and t['id']==ident and t['hash']==h and t['actor']==actor and t['expires']>time.time(),'确认已失效，请刷新页面')
   if action=='retry':
    require(delivery_ready and row['state'] in ('approved_pending_publish','withdraw_pending'),'没有待核对的发布')
    require(db.execute("SELECT 1 FROM outbox WHERE id=? AND hash=? AND state IN ('pending','sending')",(ident,h)).fetchone(),'缺少原发布记录')
    state=row['state']
   elif action=='approve':
    require(delivery_ready,'主站数据发布连接尚未完成，不能批准上线');require(row['state']=='pending_review','稿件不是待审状态');require(doc['fact_check']['checked_at']<=time.time()+60<doc['fact_check']['valid_until'],'事实核查已过期，须重新核查')
    state='approved_pending_publish'
   elif action=='reject':require(row['state']=='pending_review','只能驳回待审稿');state='rejected'
   else:
    require(not db.execute("SELECT 1 FROM outbox WHERE id=? AND state='sending'",(ident,)).fetchone(),'发布结果尚未确认，请先刷新核对再撤稿')
    require(row['state'] in ('approved_pending_publish','published'),'没有可撤回的版本')
    state='withdrawn' if row['state']=='approved_pending_publish' else 'withdraw_pending'
    if state=='withdraw_pending':require(delivery_ready,'主站连接未就绪，不能声称撤稿完成')
    else:db.execute("UPDATE outbox SET state='cancelled' WHERE id=? AND hash=? AND state='pending'",(ident,h))
   db.execute('DELETE FROM tokens WHERE token=?',(token_hash,));db.execute('INSERT INTO decisions(id,hash,action,actor,at) VALUES(?,?,?,?,?)',(ident,h,action,actor,int(time.time())))
   db.execute('UPDATE heads SET state=? WHERE id=?',(state,ident))
   if action=='approve' or action=='withdraw' and state=='withdraw_pending':db.execute('INSERT INTO outbox VALUES(?,?,?,?,?,?)',(digest([ident,h,action]),ident,h,action,'pending',int(time.time())))
  return {'id':ident,'hash':h,'state':state}
def render(doc):
 validate(doc);parts=[]
 for lang in LANGS:
  d=doc['languages'][lang];parts.append('<article lang="'+lang+'"><h2>'+html.escape(d['title'])+'</h2><p>'+html.escape(d['summary'])+'</p><p class="byline">'+html.escape(d['byline'])+'</p>'+''.join('<p>'+html.escape(p)+'</p>' for p in d['body'].split('\n') if p.strip())+'</article>')
 return '<div class="languages">'+''.join(parts)+'</div><h2>来源</h2><ul>'+''.join('<li><a target="_blank" rel="noopener" href="'+html.escape(u,quote=True)+'">'+html.escape(u)+'</a></li>' for u in doc['sources'])+'</ul>'
def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['validate','enqueue','inspect']);p.add_argument('file_or_id');p.add_argument('--root',default=str(Path(__file__).parent/'news-data'));p.add_argument('--expected');a=p.parse_args()
 if a.operation=='inspect':result=Store(a.root).get(a.file_or_id)[0]
 else:
  doc=json.loads(Path(a.file_or_id).read_text());validate(doc);result={'id':doc['id'],'hash':digest(doc)}
  if a.operation=='enqueue':result=Store(a.root).enqueue(doc,a.expected)
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
