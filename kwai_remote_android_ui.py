#!/usr/bin/env python3
import os,subprocess,urllib.parse,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
TOKEN=os.environ["REMOTE_ANDROID_TOKEN"]
def adb(*a): return subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20).stdout
SHOT_LOCK=threading.Lock()
SHOT_CACHE={"bytes":b"","at":0.0}
PAGE="""<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>Anthares Remote Android</title><style>body{font-family:sans-serif;max-width:520px;margin:auto;background:#111;color:#eee}img{width:100%;touch-action:none}button,input{font-size:18px;padding:10px;margin:4px}</style><h3>Android remoto — Kwai</h3><img id=s><div><button onclick="key(4)">Voltar</button><button onclick="key(3)">Home</button><button onclick="kwai()">Abrir Kwai</button><button onclick="fixkwai()">Reiniciar Kwai</button><button onclick="diag()">Diagnosticar</button><button onclick="done()">Concluir login</button></div><input id=t placeholder='Texto'><button onclick="txt()">Digitar</button><script>const q=new URLSearchParams(location.search),t=q.get('t'),s=document.getElementById('s');let loading=false;async function refresh(){if(loading)return;loading=true;try{let r=await fetch('/shot?t='+encodeURIComponent(t)+'&v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(r.status);let b=await r.blob(),u=URL.createObjectURL(b),old=s.dataset.url;s.src=u;s.dataset.url=u;if(old)URL.revokeObjectURL(old)}catch(e){console.warn('screenshot',e)}finally{loading=false}}setInterval(refresh,3500);refresh();s.onclick=e=>{let r=s.getBoundingClientRect();fetch('/tap?t='+encodeURIComponent(t)+'&x='+Math.round((e.clientX-r.left)*s.naturalWidth/r.width)+'&y='+Math.round((e.clientY-r.top)*s.naturalHeight/r.height),{method:'POST'}).then(refresh)};function key(k){fetch('/key?t='+encodeURIComponent(t)+'&k='+k,{method:'POST'}).then(refresh)}function kwai(){fetch('/kwai?t='+encodeURIComponent(t),{method:'POST'}).then(()=>setTimeout(refresh,1200))}function fixkwai(){fetch('/fixkwai?t='+encodeURIComponent(t),{method:'POST'}).then(()=>setTimeout(refresh,2500))}async function diag(){let r=await fetch('/diag?t='+encodeURIComponent(t),{cache:'no-store'});let x=await r.text();let p=document.getElementById('diag');if(!p){p=document.createElement('pre');p.id='diag';p.style='white-space:pre-wrap';document.body.appendChild(p)}p.textContent=x}function txt(){fetch('/text?t='+encodeURIComponent(t),{method:'POST',body:document.getElementById('t').value}).then(refresh)}async function done(){let b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes('Concluir'));b.disabled=true;b.textContent='Confirmando...';try{let r=await fetch('/done?t='+encodeURIComponent(t),{method:'POST',cache:'no-store'});if(!r.ok)throw Error(r.status);let j=await r.json();if(!j.ok)throw Error('sem confirmação');b.textContent='CONFIRMADO';document.body.insertAdjacentHTML('beforeend','<p><b>CONFIRMADO PELO SERVIDOR.</b> Pode fechar esta aba.</p>')}catch(e){b.disabled=false;b.textContent='Tentar concluir novamente';document.body.insertAdjacentHTML('beforeend','<p>Falhou ao confirmar. Clique novamente.</p>')}}</script>"""
class H(BaseHTTPRequestHandler):
 def ok(self): return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("t",[""])[0]==TOKEN
 def do_GET(self):
  if not self.ok(): self.send_response(403);self.end_headers();return
  if self.path.startswith("/shot"):
   with SHOT_LOCK:\n    now=time.monotonic()\n    if now-SHOT_CACHE["at"]>2.5 or not SHOT_CACHE["bytes"]:\n     try:\n      b=adb("exec-out","screencap","-p")\n      if b.startswith(b"\\x89PNG"):\n       SHOT_CACHE["bytes"]=b;SHOT_CACHE["at"]=now\n     except (subprocess.TimeoutExpired,OSError): pass\n    b=SHOT_CACHE["bytes"]\n   self.send_response(200);self.send_header("Content-Type","image/png");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
  if self.path.startswith("/diag"):
   cmds=[("activity",("shell","dumpsys","activity","activities")),("process",("shell","pidof","com.kwai.video")),("package",("shell","dumpsys","package","com.kwai.video")),("logcat",("logcat","-d","-t","350"))]
   parts=[]
   for name,args in cmds:
    out=adb(*args).decode("utf-8","replace")
    if name=="activity": out="\n".join(x for x in out.splitlines() if "mResumedActivity" in x or "topResumedActivity" in x or "com.kwai.video" in x)[-6000:]
    elif name=="package": out="\n".join(x for x in out.splitlines() if any(k in x.lower() for k in ("version","abi","enabled","stopped","installer")))[-6000:]
    elif name=="logcat": out="\n".join(x for x in out.splitlines() if any(k in x.lower() for k in ("kwai","kuaishou","androidruntime","fatal exception","crash","anr","native bridge","gms","integrity","ssl","network")))[-12000:]
    parts.append("## "+name+"\n"+out)
   b="\n".join(parts).encode();self.send_response(200);self.send_header("Content-Type","text/plain; charset=utf-8");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers();self.wfile.write(PAGE.encode())
 def do_POST(self):
  if not self.ok(): self.send_response(403);self.end_headers();return
  u=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(u.query)
  if u.path=="/tap": adb("shell","input","tap",q["x"][0],q["y"][0])
  elif u.path=="/key": adb("shell","input","keyevent",q["k"][0])
  elif u.path=="/kwai":
   adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
  elif u.path=="/fixkwai":
   adb("shell","am","force-stop","com.kwai.video"); adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
  elif u.path=="/text":
   n=int(self.headers.get("Content-Length","0"));v=self.rfile.read(n).decode();adb("shell","input","text",v.replace(" ","%s"))
  elif u.path=="/done":
   p="/tmp/anthares-android-done";open(p,"w").write("1");os.sync()
   if not os.path.exists(p): self.send_response(500);self.end_headers();return
   self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(b'{"ok":true}');return
  self.send_response(204);self.end_headers()
 def log_message(self,*a): pass
ThreadingHTTPServer(("127.0.0.1",8765),H).serve_forever()
