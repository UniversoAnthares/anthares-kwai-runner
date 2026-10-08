#!/usr/bin/env python3
import os,subprocess,urllib.parse,threading,time,html,shutil,json,re,xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
TOKEN=os.environ["REMOTE_ANDROID_TOKEN"]

def adb_bin():
 for p in (os.environ.get("ADB"), shutil.which("adb"), os.path.join(os.environ.get("ANDROID_HOME",""),"platform-tools","adb"), "/usr/local/lib/android/sdk/platform-tools/adb"):
  if p and os.path.isfile(p) and os.access(p,os.X_OK): return p
 raise FileNotFoundError("adb executable not found")

def adb(*a, timeout=4, check=False):
 p=subprocess.run([adb_bin(),*a],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 if check and p.returncode!=0:
  raise RuntimeError(p.stdout.decode("utf-8","replace")[-1000:])
 return p.stdout

def android_ready():
 try:
  dev=adb("get-state",timeout=1.5).decode("utf-8","replace").strip()
  if dev!="device": return False
  boot=adb("shell","getprop","sys.boot_completed",timeout=1.5).decode("utf-8","replace").strip()
  return boot=="1"
 except Exception:
  return False

def device_size():
 try:
  out=adb("shell","wm","size",timeout=2).decode("utf-8","replace")
  m=re.findall(r"(\d+)x(\d+)",out)
  if m:
   return tuple(map(int,m[-1]))
 except Exception:
  pass
 return (1080,1920)

def tap_xy(x,y):
 x=max(0,int(x)); y=max(0,int(y))
 adb("shell","input","touchscreen","tap",str(x),str(y),timeout=4,check=True)
 print(f"REMOTE_TAP x={x} y={y}",flush=True)

def ui_nodes():
 adb("shell","uiautomator","dump","/sdcard/anthares-remote-ui.xml",timeout=10)
 raw=adb("exec-out","cat","/sdcard/anthares-remote-ui.xml",timeout=4)
 root=ET.fromstring(raw)
 return list(root.iter("node"))

def node_label(n):
 return ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip()

def node_center(n):
 m=re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.get("bounds","") or "")
 if not m: return None
 a,b,c,d=map(int,m.groups())
 if c<=a or d<=b: return None
 return ((a+c)//2,(b+d)//2)

def tap_matching(nodes, patterns):
 for n in nodes:
  label=node_label(n).lower()
  rid=(n.get("resource-id") or "").lower()
  if any(re.search(p,label,re.I) or re.search(p,rid,re.I) for p in patterns):
   c=node_center(n)
   if c:
    tap_xy(*c)
    return True
 return False

AUTO_LOCK=threading.Lock()
AUTO_STATE={"last":"","at":0.0}

def onboarding_watcher():
 while True:
  time.sleep(1.0)
  if not android_ready():
   continue
  try:
   nodes=ui_nodes()
   text=" ".join(node_label(n) for n in nodes)
   low=text.lower()
   now=time.monotonic()
   with AUTO_LOCK:
    if now-AUTO_STATE["at"]<0.8:
     continue

   action=None
   if "skip the preparation" in low:
    if tap_matching(nodes,[r"^yes,?\s*skip$",r"yes.*skip"]): action="KWAI_AUTO_YES_SKIP"
   elif "allow kwai to send you notifications" in low or "send you notifications" in low:
    if tap_matching(nodes,[r"don.?t allow",r"não permitir",r"permission_deny_button"]): action="KWAI_AUTO_NOTIFICATION_DENY"
   elif "choose like or dislike" in low or "let us know you better" in low:
    w,h=device_size(); tap_xy(w*0.75,h*0.925); action="KWAI_AUTO_RIGHT_HEART"
   elif "swipe up to watch more" in low or "deslize para cima" in low:
    w,h=device_size(); adb("shell","input","swipe",str(int(w*.5)),str(int(h*.75)),str(int(w*.5)),str(int(h*.30)),"450",timeout=4,check=True); action="KWAI_AUTO_SWIPE_UP"
   elif "resource downloading" in low and "hide" in low:
    if tap_matching(nodes,[r"^hide$"]): action="KWAI_AUTO_RESOURCE_HIDE"

   if action:
    with AUTO_LOCK:
     AUTO_STATE["last"]=action; AUTO_STATE["at"]=time.monotonic()
    print(action,flush=True)
    time.sleep(1.0)
  except Exception as e:
   print("AUTO_WATCH_WARNING",type(e).__name__,flush=True)

SHOT_LOCK=threading.Lock()
SHOT_CACHE={"bytes":b"","at":0.0,"ok_at":0.0}

def waiting_svg(msg="Android inicializando..."):
 safe=html.escape(msg)
 return ("<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1920' viewBox='0 0 1080 1920'>"
         "<rect width='1080' height='1920' fill='#111'/><text x='540' y='900' text-anchor='middle' fill='#fff' "
         "font-family='sans-serif' font-size='54'>"+safe+"</text><text x='540' y='980' text-anchor='middle' fill='#aaa' "
         "font-family='sans-serif' font-size='34'>A tela aparecerá automaticamente quando o emulador estiver pronto.</text></svg>").encode()

PAGE="""<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>Anthares Remote Android</title><style>body{font-family:sans-serif;max-width:520px;margin:auto;background:#111;color:#eee}#wrap{position:relative}img{width:100%;touch-action:none;background:#111;user-select:none;-webkit-user-drag:none;cursor:crosshair}#mark{position:absolute;width:18px;height:18px;border:2px solid #ff3b30;border-radius:50%;transform:translate(-50%,-50%);pointer-events:none;display:none}button,input{font-size:18px;padding:10px;margin:4px}#state{padding:8px 4px;color:#bbb}</style><h3>Android remoto — Kwai</h3><div id=state>Conectando ao Android...</div><div id=wrap><img id=s draggable=false><div id=mark></div></div><div><button onclick="key(4)">Voltar</button><button onclick="key(3)">Home</button><button onclick="kwai()">Abrir Kwai</button><button onclick="fixkwai()">Reiniciar Kwai</button><button onclick="diag()">Diagnosticar</button><button onclick="done()">Concluir login</button></div><input id=t placeholder='Texto'><button onclick="txt()">Digitar</button><script>
const q=new URLSearchParams(location.search),t=q.get('t'),s=document.getElementById('s'),state=document.getElementById('state'),mark=document.getElementById('mark');let loading=false,errors=0,lastGood=0,tapBusy=false;
async function timedFetch(url,opt={}){let c=new AbortController(),tm=setTimeout(()=>c.abort(),4500);try{return await fetch(url,{...opt,signal:c.signal,cache:'no-store'})}finally{clearTimeout(tm)}}
async function refresh(){if(loading)return;loading=true;try{let r=await timedFetch('/shot?t='+encodeURIComponent(t)+'&v='+Date.now());if(!r.ok)throw Error(r.status);errors=0;let ready=r.headers.get('X-Android-Ready')==='1';state.textContent=ready?'Android pronto':'Android inicializando...';let b=await r.blob(),u=URL.createObjectURL(b),old=s.dataset.url;s.src=u;s.dataset.url=u;lastGood=Date.now();if(old)URL.revokeObjectURL(old)}catch(e){errors++;state.textContent=errors<3?'Reconectando à tela...':'Tela temporariamente indisponível — tentando novamente';console.warn('screenshot',e)}finally{loading=false}}
setInterval(refresh,1000);refresh();
async function sendTap(e){e.preventDefault();if(tapBusy)return;let r=s.getBoundingClientRect(),rx=(e.clientX-r.left)/r.width,ry=(e.clientY-r.top)/r.height;if(rx<0||rx>1||ry<0||ry>1)return;tapBusy=true;mark.style.left=(rx*100)+'%';mark.style.top=(ry*100)+'%';mark.style.display='block';state.textContent='Enviando toque...';try{let rr=await timedFetch('/tap?t='+encodeURIComponent(t)+'&rx='+rx.toFixed(6)+'&ry='+ry.toFixed(6),{method:'POST'});if(!rr.ok)throw Error(rr.status);state.textContent='Toque enviado';setTimeout(refresh,120);setTimeout(refresh,450);setTimeout(refresh,900)}catch(err){state.textContent='Falha no toque — tente novamente';console.warn('tap',err)}finally{setTimeout(()=>{tapBusy=false;mark.style.display='none'},180)}}
s.addEventListener('pointerup',sendTap);s.addEventListener('dragstart',e=>e.preventDefault());
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
    if ready and (now-SHOT_CACHE["at"]>0.65 or not SHOT_CACHE["bytes"]):
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
   with AUTO_LOCK: auto=dict(AUTO_STATE)
   b=json.dumps({"android_ready":android_ready(),"has_frame":bool(SHOT_CACHE["bytes"]),"auto":auto}).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
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
   with AUTO_LOCK: parts.append("## automation\n"+json.dumps(AUTO_STATE))
   b="\n".join(parts).encode();self.send_response(200);self.send_header("Content-Type","text/plain; charset=utf-8");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b);return
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers();self.wfile.write(PAGE.encode())
 def do_POST(self):
  if not self.ok(): self.send_response(403);self.end_headers();return
  u=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(u.query)
  try:
   if u.path=="/tap":
    if "rx" in q and "ry" in q:
     w,h=device_size(); x=round(float(q["rx"][0])*w); y=round(float(q["ry"][0])*h)
    else:
     x=int(q["x"][0]); y=int(q["y"][0])
    tap_xy(x,y)
   elif u.path=="/key": adb("shell","input","keyevent",q["k"][0],check=True)
   elif u.path=="/kwai": adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1",check=True)
   elif u.path=="/fixkwai": adb("shell","am","force-stop","com.kwai.video",check=True);adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1",check=True)
   elif u.path=="/text":
    n=int(self.headers.get("Content-Length","0"));v=self.rfile.read(n).decode();adb("shell","input","text",v.replace("%","%25").replace(" ","%s"),check=True)
   elif u.path=="/done":
    p="/tmp/anthares-android-done";open(p,"w").write("1");os.sync();self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(b'{"ok":true}');return
   self.send_response(204);self.send_header("Cache-Control","no-store");self.end_headers()
  except Exception as e:
   self.send_response(503);self.send_header("Content-Type","text/plain; charset=utf-8");self.end_headers();self.wfile.write(("remote command failed: "+repr(e)).encode())
 def log_message(self,*a): pass

threading.Thread(target=onboarding_watcher,daemon=True).start()
ThreadingHTTPServer(("127.0.0.1",8765),H).serve_forever()
