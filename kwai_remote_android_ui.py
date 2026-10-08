#!/usr/bin/env python3
import os,subprocess,urllib.parse,threading,time,html,shutil,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
TOKEN=os.environ["REMOTE_ANDROID_TOKEN"]

def adb_bin():
 for p in (os.environ.get("ADB"), shutil.which("adb"), os.path.join(os.environ.get("ANDROID_HOME",""),"platform-tools","adb"), "/usr/local/lib/android/sdk/platform-tools/adb"):
  if p and os.path.isfile(p) and os.access(p,os.X_OK): return p
 raise FileNotFoundError("adb executable not found")

def adb(*a, timeout=4):
 return subprocess.run([adb_bin(),*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout).stdout

def android_ready():
 try:
  dev=adb("get-state",timeout=1.5).decode("utf-8","replace").strip()
  if dev!="device": return False
  boot=adb("shell","getprop","sys.boot_completed",timeout=1.5).decode("utf-8","replace").strip()
  return boot=="1"
 except Exception:
  return False

SHOT_LOCK=threading.Lock()
SHOT_CACHE={"bytes":b"","at":0.0,"ok_at":0.0}

def waiting_svg(msg="Android inicializando..."):
 safe=html.escape(msg)
 return ("<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1920' viewBox='0 0 1080 1920'>"
         "<rect width='1080' height='1920' fill='#111'/><text x='540' y='900' text-anchor='middle' fill='#fff' "
         "font-family='sans-serif' font-size='54'>"+safe+"</text><text x='540' y='980' text-anchor='middle' fill='#aaa' "
         "font-family='sans-serif' font-size='34'>A tela aparecerá automaticamente quando o emulador estiver pronto.</text></svg>").encode()

PAGE="""<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>Anthares Remote Android</title><style>body{font-family:sans-serif;max-width:520px;margin:auto;background:#111;color:#eee}img{width:100%;touch-action:none;background:#111}button,input{font-size:18px;padding:10px;margin:4px}#state{padding:8px 4px;color:#bbb}</style><h3>Android remoto — Kwai</h3><div id=state>Conectando ao Android...</div><img id=s><div><button onclick="key(4)">Voltar</button><button onclick="key(3)">Home</button><button onclick="kwai()">Abrir Kwai</button><button onclick="fixkwai()">Reiniciar Kwai</button><button onclick="diag()">Diagnosticar</button><button onclick="done()">Concluir login</button></div><input id=t placeholder='Texto'><button onclick="txt()">Digitar</button><script>
const q=new URLSearchParams(location.search),t=q.get('t'),s=document.getElementById('s'),state=document.getElementById('state');let loading=false,errors=0,lastGood=0;
async function timedFetch(url,opt={}){let c=new AbortController(),tm=setTimeout(()=>c.abort(),4500);try{return await fetch(url,{...opt,signal:c.signal})}finally{clearTimeout(tm)}}
async function refresh(){if(loading)return;loading=true;try{let r=await timedFetch('/shot?t='+encodeURIComponent(t)+'&v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(r.status);errors=0;let ready=r.headers.get('X-Android-Ready')==='1';state.textContent=ready?'Android pronto':'Android inicializando...';let b=await r.blob(),u=URL.createObjectURL(b),old=s.dataset.url;s.src=u;s.dataset.url=u;lastGood=Date.now();if(old)URL.revokeObjectURL(old)}catch(e){errors++;state.textContent=errors<3?'Reconectando à tela...':'Tela temporariamente indisponível — tentando novamente';console.warn('screenshot',e)}finally{loading=false}}
setInterval(refresh,1500);refresh();
s.onclick=e=>{let r=s.getBoundingClientRect();fetch('/tap?t='+encodeURIComponent(t)+'&x='+Math.round((e.clientX-r.left)*s.naturalWidth/r.width)+'&y='+Math.round((e.clientY-r.top)*s.naturalHeight/r.height),{method:'POST'}).then(refresh)};
function key(k){fetch('/key?t='+encodeURIComponent(t)+'&k='+k,{method:'POST'}).then(refresh)}function kwai(){fetch('/kwai?t='+encodeURIComponent(t),{method:'POST'}).then(()=>setTimeout(refresh,600))}function fixkwai(){fetch('/fixkwai?t='+encodeURIComponent(t),{method:'POST'}).then(()=>setTimeout(refresh,1200))}
async function diag(){let r=await fetch('/diag?t='+encodeURIComponent(t),{cache:'no-store'});let x=await r.text();let p=document.getElementById('diag');if(!p){p=document.createElement('pre');p.id='diag';p.style='white-space:pre-wrap';document.body.appendChild(p)}p.textContent=x}
async function txt(){let v=document.getElementById('t').value,b=[...document.querySelectorAll('button')].find(x=>x.textContent==='Digitar');b.disabled=true;try{let r=await fetch('/text?t='+encodeURIComponent(t),{method:'POST',body:v});if(!r.ok)throw Error(r.status);state.textContent='Texto enviado ao Android';setTimeout(refresh,350)}catch(e){state.textContent='Falha ao enviar texto'}finally{b.disabled=false}}
async function done(){let b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes('Concluir'));b.disabled=true;b.textContent='Confirmando...';try{let r=await fetch('/done?t='+encodeURIComponent(t),{method:'POST',cache:'no-store'});if(!r.ok)throw Error(r.status);let j=await r.json();if(!j.ok)throw Error('sem confirmação');b.textContent='CONFIRMADO';document.body.insertAdjacentHTML('beforeend','<p><b>CONFIRMADO PELO SERVIDOR.</b> Pode fechar esta aba.</p>')}catch(e){b.disabled=false;b.textContent='Tentar concluir novamente';document.body.insertAdjacentHTML('beforeend','<p>Falhou ao confirmar. Clique novamente.</p>')}}</script>"""

class H(BaseHTTPRequestHandler):
 def ok(self): return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("t",[""])[0]==TOKEN
 def do_GET(self):
  if not self.ok(): self.send_response(403);self.end_headers();return
  if self.path.startswith("/shot"):
   ready=android_ready()
   with SHOT_LOCK:
    now=time.monotonic()
    if ready and (now-SHOT_CACHE["at"]>1.0 or not SHOT_CACHE["bytes"]):
     try:
      b=adb("exec-out","screencap","-p",timeout=2.5)
      if b.startswith(b"\x89PNG"):
       SHOT_CACHE["bytes"]=b;SHOT_CACHE["at"]=now;SHOT_CACHE["ok_at"]=now
     except Exception:
      pass
    b=SHOT_CACHE["bytes"]
   if not b:
    b=waiting_svg("Android inicializando..." if not ready else "Android pronto; aguardando primeira imagem...");ctype="image/svg+xml"
   else:
    ctype="image/png"
   self.send_response(200);self.send_header("Content-Type",ctype);self.send_header("X-Android-Ready","1" if ready else "0");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
  if self.path.startswith("/health"):
   b=json.dumps({"android_ready":android_ready(),"has_frame":bool(SHOT_CACHE["bytes"])}).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
  if self.path.startswith("/diag"):
   cmds=[("activity",("shell","dumpsys","activity","activities")),("process",("shell","pidof","com.kwai.video")),("package",("shell","dumpsys","package","com.kwai.video")),("logcat",("logcat","-d","-t","350"))]
   parts=[]
   for name,args in cmds:
    try: out=adb(*args,timeout=6).decode("utf-8","replace")
    except Exception as e: out="ERROR: "+repr(e)
    if name=="activity": out="\n".join(x for x in out.splitlines() if "mResumedActivity" in x or "topResumedActivity" in x or "com.kwai.video" in x)[-6000:]
    elif name=="package": out="\n".join(x for x in out.splitlines() if any(k in x.lower() for k in ("version","abi","enabled","stopped","installer")))[-6000:]
    elif name=="logcat": out="\n".join(x for x in out.splitlines() if any(k in x.lower() for k in ("kwai","kuaishou","androidruntime","fatal exception","crash","anr","native bridge","gms","integrity","ssl","network")))[-12000:]
    parts.append("## "+name+"\n"+out)
   b="\n".join(parts).encode();self.send_response(200);self.send_header("Content-Type","text/plain; charset=utf-8");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers();self.wfile.write(PAGE.encode())
 def do_POST(self):
  if not self.ok(): self.send_response(403);self.end_headers();return
  u=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(u.query)
  try:
   if u.path=="/tap": adb("shell","input","tap",q["x"][0],q["y"][0])
   elif u.path=="/key": adb("shell","input","keyevent",q["k"][0])
   elif u.path=="/kwai": adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
   elif u.path=="/fixkwai": adb("shell","am","force-stop","com.kwai.video");adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
   elif u.path=="/text":
    n=int(self.headers.get("Content-Length","0"));v=self.rfile.read(n).decode();adb("shell","input","text",v.replace("%","%25").replace(" ","%s"))
   elif u.path=="/done":
    p="/tmp/anthares-android-done";open(p,"w").write("1");os.sync();self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(b'{"ok":true}');return
   self.send_response(204);self.end_headers()
  except Exception as e:
   self.send_response(503);self.send_header("Content-Type","text/plain; charset=utf-8");self.end_headers();self.wfile.write(("remote command failed: "+repr(e)).encode())
 def log_message(self,*a): pass

ThreadingHTTPServer(("127.0.0.1",8765),H).serve_forever()
