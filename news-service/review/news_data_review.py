"""Review extension. Existing Access verifier unchanged; no publishing on startup."""
import html,json,os,time
from pathlib import Path
from urllib.parse import urlsplit,unquote
from news_data import Store,validate,render,digest,LANGS,BYLINES,require
from news_delivery import Delivery
PATH='/news-data/'
STYLE='*{box-sizing:border-box}code{overflow-wrap:anywhere}body{font:16px/1.7 system-ui;background:#f6f7f3;color:#223d33;margin:auto;padding:20px;max-width:1400px}a{color:#176d55}button,textarea{font:inherit}button{padding:12px;margin:6px}button:disabled{opacity:.5}.languages{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.languages article{background:white;padding:18px;border:1px solid #ccd9d1;border-radius:12px;overflow-wrap:anywhere}h2{font-size:21px}.notice{padding:16px;background:#fff4d4}textarea{width:100%;min-height:220px;box-sizing:border-box}@media(max-width:900px){.languages{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:550px){.languages{grid-template-columns:1fr}body{padding:14px}}'
def shell(title,body):return ('<!doctype html><html lang="zh-Hans"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style><main><a href="/">审核首页</a> · <a href="'+PATH+'">数据新闻</a><h1>'+html.escape(title)+'</h1>'+body+'</main></html>').encode()
def demo():
 texts={'zh-Hans':('四语数据稿件展示','这是界面示例，不是新闻稿，不会入队或发布。'),'zh-Hant':('四語資料稿件展示','這是介面範例，不是新聞稿，不會入列或發布。'),'en':('Four-language data preview','This is an interface example, not an article. It cannot be queued or published.'),'ja':('4言語のデータ原稿プレビュー','画面の例です。ニュース原稿ではなく、審査待ち登録や公開はできません。')}
 return {'schema':'news-data-v1','id':'INTERFACE-DEMO','category':'learning','languages':{k:{'title':v[0],'summary':v[1],'body':v[1],'byline':BYLINES[k]}for k,v in texts.items()},'sources':['https://nice.okinawa/'],'fact_check':{'checked_at':int(time.time()),'valid_until':int(time.time())+3600,'note':'Interface-only demo, not a factual article; no publication.'}}
class App:
 def __init__(self,s):self.s=s;self.root=Path(s.__file__).parent/'news-data';self.store=Store(self.root);self.delivery=Delivery(self.store)
 def identity(self,headers,write=False):
  if os.environ.get('REVIEW_TRUST_TEST_ACCESS')=='1':raise PermissionError('production test bypass forbidden')
  if write and headers.get('Origin')!='https://review.nice.okinawa':raise PermissionError('origin required')
  self.s.validate_origin(headers);actor=self.s.access_identity(headers);require(actor.get('email'),'Access身份缺失');return actor['email']
 def ready(self):
  return self.delivery.ready()
 def listing(self):
  pending=[];history=[]
  for row in self.store.listing():
   r,d=self.store.get(row['id']);item='<section><h2><a href="'+PATH+html.escape(r['id'])+'">'+html.escape(r['id'])+'</a> · '+html.escape(r['state'])+'</h2>'+render(d)+'</section>'
   (pending if r['state']=='pending_review' else history).append(item)
  return shell('新闻数据稿件','<p class="notice">只有本人审核通过的精确版本才会发布；收到主站回执后才标为已上线。</p><p><a href="'+PATH+'demo">查看只读四语界面示例</a></p><h2>待审核</h2>'+(''.join(pending) or '<p>暂无待审数据稿件。</p>')+'<h2>历史</h2>'+(''.join(history) or '<p>暂无记录。</p>'))
 def page(self,ident,actor):
  # Read receipts only on refresh; never publish during a GET.
  try:self.delivery.reconcile(ident)
  except Exception:pass # Keep the exact-version page readable during an outage.
  row,doc=self.store.get(ident);token=self.store.token(ident,actor);state=row['state'];active=state=='pending_review';ready=self.ready();body='<p>精确版本：<code>'+row['hash']+'</code> · 状态：'+html.escape(state)+'</p>'+render(doc)+'<p class="notice">'+('批准后提交精确版本发布；收到回执才记上线。' if ready else '主站连接尚未接通，批准上线暂不可用；第2车接通后再审核。')+'</p><button data-action="reject" '+('' if active else 'disabled')+'>驳回</button><button data-action="approve" '+('' if active and ready else 'disabled')+'>通过并上线</button><button data-action="withdraw" '+('' if state=='approved_pending_publish' or state=='published' and ready else 'disabled')+'>撤回本版</button><p id="status" role="status"></p>'
  if state in ('approved_pending_publish','withdraw_pending'):body+='<button data-action="retry">核对并重试原发布</button>'
  payload=json.dumps({'id':ident,'hash':row['hash'],'token':token},ensure_ascii=True).replace('<','\\u003c')
  body+='''<script>const payload='''+payload+''';document.querySelectorAll('[data-action]').forEach(b=>b.onclick=async()=>{if(b.dataset.action==='withdraw'&&!confirm('确定撤回这个版本吗？'))return;document.querySelectorAll('button').forEach(x=>x.disabled=true);try{const r=await fetch('/news-data/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload,action:b.dataset.action})});const x=await r.json();if(!r.ok)throw Error(x.error||'操作未确认');location.reload()}catch(e){document.getElementById('status').textContent=e.message+'。请刷新后核对，不要重复提交。'}});</script>'''
  return shell(doc['languages']['zh-Hans']['title'],body)
 def decision(self,p,headers):
  actor=self.identity(headers,True);require(isinstance(p,dict) and set(p)=={'id','hash','action','token'},'请求字段错误');require(all(isinstance(v,str) for v in p.values()),'请求格式错误')
  if p['action']=='withdraw':self.delivery.reconcile(p['id'])
  result=self.store.decide(p['id'],p['hash'],p['action'],actor,p['token'],self.ready())
  if result['state'] in ('approved_pending_publish','withdraw_pending'):
   self.delivery.deliver(p['id']);result=self.store.get(p['id'])[0]
  return result
def mount(s):
 if getattr(s,'_news_data',None):return s._news_data
 app=App(s);s._news_data=app;oldget=s.Handler.do_GET;oldpost=s.Handler.do_POST;oldhome=s.render_home
 def send(h,body):
  h.send_response(200)
  for k,v in {'Content-Type':'text/html; charset=utf-8','Content-Length':str(len(body)),'Cache-Control':'no-store','X-Robots-Tag':'noindex,nofollow','X-Frame-Options':'DENY','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"}.items():h.send_header(k,v)
  h.end_headers();h.wfile.write(body)
 def get(h):
  p=urlsplit(h.path)
  if not p.path.startswith(PATH):return oldget(h)
  try:
   actor=app.identity(h.headers);require(not p.query,'不接受查询参数');ident=unquote(p.path[len(PATH):])
   if not ident:return send(h,app.listing())
   if ident=='demo':return send(h,shell('只读界面示例', '<p class="notice">不是实际稿件，不会入队或发布，没有审批按钮。</p>'+render(demo())))
   return send(h,app.page(ident,actor))
  except PermissionError:return h.send_json({'error':'Access required'},403)
  except Exception:return h.send_json({'error':'稿件或版本无法核实，请刷新并联系维护人员'},409)
 def post(h):
  if urlsplit(h.path).path!=PATH+'decision':return oldpost(h)
  try:
   app.identity(h.headers,True);require(h.path==PATH+'decision','请求地址错误');n=int(h.headers.get('Content-Length','0'));require(0<n<=4096 and h.headers.get('Content-Type')=='application/json','请求格式错误');return h.send_json(app.decision(json.loads(h.rfile.read(n)),h.headers))
  except PermissionError:return h.send_json({'error':'Access required'},403)
  except Exception as e:return h.send_json({'error':str(e)},409)
 def home():
  b=oldhome();rows=app.store.listing();links=''.join('<li><a href="'+PATH+html.escape(r['id'])+'">'+html.escape(r['id'])+' · 四语数据稿件</a></li>' for r in rows if r['state']=='pending_review');section='<section><h2>数据新闻</h2><a href="'+PATH+'">稿件列表与四语预览</a><ul>'+links+'</ul></section>'
  return b.replace(b'</main>',section.encode()+b'</main>',1)
 s.Handler.do_GET=get;s.Handler.do_POST=post;s.render_home=home;return app
