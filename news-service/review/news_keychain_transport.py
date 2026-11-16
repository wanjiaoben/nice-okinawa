"""macOS transport: credential stays in Keychain and this process's memory."""
import ctypes,json,re,sys,urllib.request
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def main():
 p=json.load(sys.stdin);path=p['path'];payload=p.get('payload')
 if not re.fullmatch(r'/__news/(publish|status(?:\?event_key=[a-f0-9]{64})?)',path):raise ValueError('path')
 s=ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
 f=s.SecKeychainFindGenericPassword
 f.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_void_p),ctypes.c_void_p];f.restype=ctypes.c_int32
 service=b'nice-news-data-v1-publish';account=b'CC-mini';length=ctypes.c_uint32();pointer=ctypes.c_void_p()
 status=f(None,len(service),service,len(account),account,ctypes.byref(length),ctypes.byref(pointer),None)
 if status:raise RuntimeError('Keychain unavailable')
 token=ctypes.string_at(pointer,length.value).decode();s.SecKeychainItemFreeContent(None,pointer)
 data=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode() if payload is not None else None
 request=urllib.request.Request('https://nice-news-data-v1.gerheidicn.workers.dev'+path,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 with urllib.request.build_opener(NoRedirect).open(request,timeout=15) as response:result=json.load(response)
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception:print('{"error":"delivery_unconfirmed"}');sys.exit(1)
