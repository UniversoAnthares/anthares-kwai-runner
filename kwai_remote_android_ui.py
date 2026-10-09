#!/usr/bin/env python3
import json, os, re, shutil, subprocess, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ["REMOTE_ANDROID_TOKEN"]
SHOT_LOCK = threading.Lock()
SHOT_CACHE = {"bytes": b"", "at": 0.0}
TOUCH_VISUALS_DISABLED = False
TOUCH_VISUALS_LAST_CHECK = 0.0


def adb_bin():
    for p in (
        os.environ.get("ADB"),
        shutil.which("adb"),
        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
        "/usr/local/lib/android/sdk/platform-tools/adb",
    ):
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    raise FileNotFoundError("adb executable not found")


def adb(*args, timeout=5, check=False):
    p = subprocess.run(
        [adb_bin(), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if check and p.returncode != 0:
        raise RuntimeError(p.stdout.decode("utf-8", "replace")[-1000:])
    return p.stdout


def android_ready():
    try:
        if adb("get-state", timeout=2).decode("utf-8", "replace").strip() != "device":
            return False
        return adb("shell", "getprop", "sys.boot_completed", timeout=2).decode("utf-8", "replace").strip() == "1"
    except Exception:
        return False


def ensure_touch_visuals_disabled():
    global TOUCH_VISUALS_DISABLED, TOUCH_VISUALS_LAST_CHECK
    if not android_ready():
        return
    now = time.monotonic()
    if TOUCH_VISUALS_DISABLED and now - TOUCH_VISUALS_LAST_CHECK < 2.0:
        return
    TOUCH_VISUALS_LAST_CHECK = now
    try:
        show = adb("shell", "settings", "get", "system", "show_touches", timeout=4).decode("utf-8", "replace").strip()
        pointer = adb("shell", "settings", "get", "system", "pointer_location", timeout=4).decode("utf-8", "replace").strip()
        if show != "0":
            adb("shell", "settings", "put", "system", "show_touches", "0", timeout=4, check=True)
        if pointer != "0":
            adb("shell", "settings", "put", "system", "pointer_location", "0", timeout=4, check=True)
        show = adb("shell", "settings", "get", "system", "show_touches", timeout=4).decode("utf-8", "replace").strip()
        pointer = adb("shell", "settings", "get", "system", "pointer_location", timeout=4).decode("utf-8", "replace").strip()
        TOUCH_VISUALS_DISABLED = show == "0" and pointer == "0"
    except Exception:
        TOUCH_VISUALS_DISABLED = False


def device_size():
    try:
        out = adb("shell", "wm", "size", timeout=3).decode("utf-8", "replace")
        m = re.findall(r"(\d+)x(\d+)", out)
        if m:
            return tuple(map(int, m[-1]))
    except Exception:
        pass
    return 1080, 1920


def safe_write(handler, data):
    try:
        handler.wfile.write(data)
    except (BrokenPipeError, ConnectionResetError):
        pass


def screenshot():
    ready = android_ready()
    if ready:
        ensure_touch_visuals_disabled()
    with SHOT_LOCK:
        now = time.monotonic()
        if ready and (not SHOT_CACHE["bytes"] or now - SHOT_CACHE["at"] >= 1.8):
            try:
                b = adb("exec-out", "screencap", "-p", timeout=5)
                if b.startswith(b"\x89PNG"):
                    SHOT_CACHE["bytes"] = b
                    SHOT_CACHE["at"] = now
            except Exception:
                pass
        return ready, SHOT_CACHE["bytes"]


PAGE = r"""<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'>
<title>Anthares Remote Android</title>
<style>
body{font-family:sans-serif;max-width:520px;margin:auto;background:#111;color:#eee}#wrap{position:relative}
img{width:100%;touch-action:none;background:#111;user-select:none;-webkit-user-drag:none;cursor:crosshair}
#mark{display:none!important}
button,input{font-size:18px;padding:10px;margin:4px}#state{padding:8px 4px;color:#bbb}pre{white-space:pre-wrap;font-size:12px}
</style>
<h3>Android remoto — Kwai</h3><div id=state>Conectando ao Android...</div>
<div id=wrap><img id=s draggable=false><div id=mark></div></div>
<div><button onclick="key(4)">Voltar</button><button onclick="key(3)">Home</button><button onclick="kwai()">Abrir Kwai</button><button onclick="fixkwai()">Reiniciar Kwai</button><button onclick="diag()">Diagnosticar</button><button onclick="done()">Concluir login</button></div>
<input id=t type=text autocomplete=off autocapitalize=off spellcheck=false placeholder='Texto para digitar no Android'><button onclick="txt()">Digitar</button><button onclick="clearText()">Limpar texto</button>
<script>
const q=new URLSearchParams(location.search),t=q.get('t'),s=document.getElementById('s'),state=document.getElementById('state'),mark=document.getElementById('mark');let loading=false,errors=0,tapBusy=false;
async function timedFetch(url,opt={}){let c=new AbortController(),tm=setTimeout(()=>c.abort(),7000);try{return await fetch(url,{...opt,signal:c.signal,cache:'no-store'})}finally{clearTimeout(tm)}}
async function refresh(){if(loading)return;loading=true;try{let r=await timedFetch('/shot?t='+encodeURIComponent(t)+'&v='+Date.now());if(!r.ok)throw Error(r.status);let ready=r.headers.get('X-Android-Ready')==='1',b=await r.blob(),u=URL.createObjectURL(b),old=s.dataset.url;s.src=u;s.dataset.url=u;if(old)URL.revokeObjectURL(old);errors=0;state.textContent=ready?'Android pronto':'Android inicializando...'}catch(e){errors++;state.textContent=errors<3?'Reconectando à tela...':'Tela temporariamente indisponível — tentando novamente'}finally{loading=false}}
setInterval(refresh,2500);refresh();
async function sendTap(e){e.preventDefault();if(tapBusy)return;let r=s.getBoundingClientRect(),rx=(e.clientX-r.left)/r.width,ry=(e.clientY-r.top)/r.height;if(rx<0||rx>1||ry<0||ry>1)return;tapBusy=true;try{let rr=await timedFetch('/tap?t='+encodeURIComponent(t)+'&rx='+rx.toFixed(6)+'&ry='+ry.toFixed(6),{method:'POST'});if(!rr.ok)throw Error(rr.status);state.textContent='Toque enviado';setTimeout(refresh,250)}catch(e){state.textContent='Falha no toque — tente novamente'}finally{setTimeout(()=>{tapBusy=false},220)}}
s.addEventListener('pointerup',sendTap);s.addEventListener('pointerdown',e=>e.preventDefault());s.addEventListener('contextmenu',e=>e.preventDefault());s.addEventListener('dragstart',e=>e.preventDefault());
function key(k){timedFetch('/key?t='+encodeURIComponent(t)+'&k='+k,{method:'POST'}).then(refresh)}
function kwai(){timedFetch('/kwai?t='+encodeURIComponent(t),{method:'POST'}).then(()=>setTimeout(refresh,600))}
function fixkwai(){timedFetch('/fixkwai?t='+encodeURIComponent(t),{method:'POST'}).then(()=>setTimeout(refresh,1200))}
async function diag(){let r=await timedFetch('/diag?t='+encodeURIComponent(t)),x=await r.text(),p=document.getElementById('diag');if(!p){p=document.createElement('pre');p.id='diag';document.body.appendChild(p)}p.textContent=x}
let textSending=false;async function txt(){if(textSending)return;textSending=true;try{let f=document.getElementById('t'),v=f.value;let r=await timedFetch('/text?t='+encodeURIComponent(t),{method:'POST',body:v});state.textContent=r.ok?'Texto enviado ao Android':'Falha ao enviar texto — conteúdo preservado';setTimeout(refresh,350)}finally{textSending=false}}
async function clearText(){let r=await timedFetch('/clear?t='+encodeURIComponent(t),{method:'POST'});state.textContent=r.ok?'Campo selecionado limpo':'Falha ao limpar campo';if(r.ok)document.getElementById('t').value='';setTimeout(refresh,350)}
async function done(){let r=await timedFetch('/done?t='+encodeURIComponent(t),{method:'POST'});if(r.ok){state.textContent='Confirmação enviada; validando autenticação no servidor.'}}
</script>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def authorized(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        return q.get("t", [""])[0] == TOKEN

    def send_bytes(self, data, content_type="text/plain; charset=utf-8", status=200, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        safe_write(self, data)

    def do_GET(self):
        if not self.authorized():
            self.send_bytes(b"forbidden", status=403)
            return
        u = urllib.parse.urlparse(self.path)
        if u.path == "/shot":
            ready, b = screenshot()
            if not b:
                b = ("<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1920'><rect width='100%' height='100%' fill='#111'/><text x='540' y='960' text-anchor='middle' fill='#fff' font-size='48'>Android inicializando...</text></svg>").encode()
                ctype = "image/svg+xml"
            else:
                ctype = "image/png"
            self.send_bytes(b, ctype, extra={"X-Android-Ready": "1" if ready else "0"})
            return
        if u.path == "/health":
            ready, b = screenshot()
            self.send_bytes(json.dumps({"android_ready": ready, "has_frame": bool(b)}).encode(), "application/json")
            return
        if u.path == "/diag":
            parts = []
            cmds = [
                ("activity", ("shell", "dumpsys", "activity", "activities")),
                ("process", ("shell", "pidof", "com.kwai.video")),
                ("connectivity", ("shell", "dumpsys", "connectivity")),
                ("logcat", ("logcat", "-d", "-t", "500")),
            ]
            for name, args in cmds:
                try:
                    out = adb(*args, timeout=8).decode("utf-8", "replace")
                except Exception as e:
                    out = "ERROR: " + type(e).__name__
                if name == "activity":
                    out = "\n".join(x for x in out.splitlines() if "topResumedActivity" in x or "com.kwai.video" in x)[-7000:]
                elif name == "connectivity":
                    out = "\n".join(x for x in out.splitlines() if any(k in x for k in ("VALIDATED", "INTERNET", "DefaultNetwork", "NetworkAgentInfo")))[-7000:]
                elif name == "logcat":
                    keys = ("kwai", "kuaishou", "unknownhost", "ssl", "cronet", "okhttp", "network", "connectexception", "sockettimeout", "http 401", "http 403", "http 500", "error_code", "onfailed", "auth", "api", "login", "aegon")
                    out = "\n".join(x for x in out.splitlines() if any(k in x.lower() for k in keys))[-30000:]
                parts.append("## " + name + "\n" + out)
            self.send_bytes("\n".join(parts).encode())
            return
        self.send_bytes(PAGE.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        if not self.authorized():
            self.send_bytes(b"forbidden", status=403)
            return
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/tap":
                w, h = device_size()
                x = round(float(q["rx"][0]) * w)
                y = round(float(q["ry"][0]) * h)
                adb("shell", "input", "touchscreen", "tap", str(x), str(y), timeout=5, check=True)
            elif u.path == "/key":
                adb("shell", "input", "keyevent", q["k"][0], timeout=5, check=True)
            elif u.path == "/kwai":
                adb("shell", "monkey", "-p", "com.kwai.video", "-c", "android.intent.category.LAUNCHER", "1", timeout=8, check=True)
            elif u.path == "/fixkwai":
                adb("shell", "am", "force-stop", "com.kwai.video", timeout=5)
                adb("shell", "monkey", "-p", "com.kwai.video", "-c", "android.intent.category.LAUNCHER", "1", timeout=8, check=True)
            elif u.path == "/clear":
                adb("shell", "input", "keycombination", "KEYCODE_CTRL_LEFT", "KEYCODE_A", timeout=5, check=True)
                adb("shell", "input", "keyevent", "KEYCODE_DEL", timeout=5, check=True)
            elif u.path == "/text":
                n = int(self.headers.get("Content-Length", "0"))
                v = self.rfile.read(n).decode("utf-8", "replace")
                if v:
                    import itertools
                    for space, chars in itertools.groupby(v, lambda c: c == " "):
                        chunk = "".join(chars)
                        if space:
                            for _ in chunk:
                                adb("shell", "input", "keyevent", "KEYCODE_SPACE", timeout=5, check=True)
                        else:
                            adb("shell", "input", "text", chunk.replace("%", "%25"), timeout=15, check=True)
            elif u.path == "/done":
                with open("/tmp/anthares-android-done", "w") as f:
                    f.write("1")
                os.sync()
                self.send_bytes(b'{"ok":true}', "application/json")
                return
            else:
                self.send_bytes(b"not found", status=404)
                return
            self.send_bytes(b"ok")
        except Exception as e:
            self.send_bytes(("error:" + type(e).__name__).encode(), status=500)


class Server(ThreadingHTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    srv = Server(("127.0.0.1", 8765), Handler)
    print("REMOTE_UI_READY", flush=True)
    srv.serve_forever()
