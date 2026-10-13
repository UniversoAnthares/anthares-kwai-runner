#!/usr/bin/env python3
import base64, json, os, secrets, signal, subprocess, tempfile, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

RESULT_PORT=int(os.environ.get('PORT','10000'))
API_PORT=RESULT_PORT
PAGE_PORT=18081
TOKEN=secrets.token_urlsafe(32)
VNC_PASSWORD=secrets.token_urlsafe(24)
ROOT=Path('/opt/anthares-brouser')
RESULT={'ok':False,'cases':[],'restart_profile':False}

def request(path,method='GET',body=None,auth=True,timeout=15):
    headers={'Authorization':f'Bearer {TOKEN}'} if auth else {}
    data=None
    if body is not None:
        headers['Content-Type']='application/json'; data=json.dumps(body).encode()
    req=urllib.request.Request(f'http://127.0.0.1:{API_PORT}{path}',data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(); return r.status,(json.loads(raw.decode()) if raw else {})
    except urllib.error.HTTPError as exc:
        raw=exc.read()
        try: payload=json.loads(raw.decode()) if raw else {}
        except Exception: payload={'raw':raw.decode(errors='replace')}
        return exc.code,payload

def wait_ready(proc,timeout=70):
    deadline=time.time()+timeout; last=None
    while time.time()<deadline:
        if proc.poll() is not None: raise RuntimeError(f'browser stack exited rc={proc.returncode}')
        try:
            code,data=request('/ready',auth=False,timeout=4); last=(code,data)
            if code==200 and data.get('ok') and data.get('chromium_running') and data.get('cdp_ready'): return data
        except Exception as exc: last=repr(exc)
        time.sleep(.5)
    raise RuntimeError(f'ready timeout last={last}')

def start_stack():
    env=os.environ.copy(); env.update({'PORT':str(API_PORT),'CONTROL_TOKEN':TOKEN,'VNC_PASSWORD':VNC_PASSWORD,'START_URL':f'http://127.0.0.1:{PAGE_PORT}/','CHROME_PROFILE_DIR':'/data/chrome-profile','MAX_READY_FAILURES':'6','SUPERVISOR_INTERVAL':'1'})
    proc=subprocess.Popen([str(ROOT/'start.sh')],cwd=ROOT,env=env); wait_ready(proc); return proc

def stop_stack(proc):
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try: proc.wait(timeout=15)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)

def run_cases():
    temp=tempfile.TemporaryDirectory(); page_root=Path(temp.name)
    page_root.joinpath('index.html').write_text("""<!doctype html><html><head><title>Anthares Render40</title></head><body><input id='qa-input' value=''><button id='qa-button' onclick=\"document.getElementById('qa-result').textContent=document.getElementById('qa-input').value\">click</button><div id='qa-result'>idle</div></body></html>""",encoding='utf-8')
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    page_server=ThreadingHTTPServer(('127.0.0.1',PAGE_PORT),lambda *a,**k:Quiet(*a,directory=str(page_root),**k)); threading.Thread(target=page_server.serve_forever,daemon=True).start()
    stack=None
    try:
        stack=start_stack()
        for path in ('/status','/page','/targets','/screenshot'):
            code,_=request(path,auth=False)
            if code!=401: raise AssertionError(f'unauthenticated {path} => {code}')
        code,status=request('/status'); assert code==200 and status.get('cdp_ready') is True and status.get('cdp_bind')=='127.0.0.1',status
        for case in range(1,41):
            value=f'render40-case-{case:02d}'; checks={}
            code,nav=request('/navigate','POST',{'url':f'http://127.0.0.1:{PAGE_PORT}/?case={case}','wait_ms':25}); checks['navigate']=code==200 and f'case={case}' in nav.get('url','')
            code,waited=request('/wait','POST',{'selector':'#qa-input','timeout_ms':5000,'visible':True}); checks['wait']=code==200 and waited.get('ok') is True
            code,typed=request('/type','POST',{'selector':'#qa-input','text':value,'clear':True,'wait_ms':10}); checks['type']=code==200 and typed.get('ok') is True and typed.get('chars')==len(value)
            code,evaluated=request('/evaluate','POST',{'expression':"document.querySelector('#qa-input').value",'return_by_value':True}); checks['evaluate']=code==200 and (evaluated.get('result') or {}).get('value')==value
            code,_=request('/click','POST',{'selector':'#qa-button','wait_ms':10}); checks['click']=code==200
            code,clicked=request('/evaluate','POST',{'expression':"document.querySelector('#qa-result').textContent",'return_by_value':True}); checks['click_effect']=code==200 and (clicked.get('result') or {}).get('value')==value
            code,shot=request('/screenshot'); png=b''
            if code==200 and shot.get('base64'): png=base64.b64decode(shot['base64'])
            checks['screenshot']=code==200 and png.startswith(b'\x89PNG\r\n\x1a\n') and len(png)>1000
            ok=all(checks.values()); RESULT['cases'].append({'case':case,'ok':ok,'checks':checks})
            if not ok: raise AssertionError(f'case {case} failed: {checks}')
        marker='render40-persist-marker-v1'
        code,set_marker=request('/evaluate','POST',{'expression':f"localStorage.setItem('anthares_render40','{marker}'); localStorage.getItem('anthares_render40')",'return_by_value':True}); assert code==200 and (set_marker.get('result') or {}).get('value')==marker,set_marker
        stop_stack(stack); stack=None; time.sleep(1); stack=start_stack()
        code,restored=request('/evaluate','POST',{'expression':"localStorage.getItem('anthares_render40')",'return_by_value':True}); RESULT['restart_profile']=code==200 and (restored.get('result') or {}).get('value')==marker
        if not RESULT['restart_profile']: raise AssertionError(f'profile restart failed: {restored}')
        with urllib.request.urlopen('http://127.0.0.1:6080/vnc.html',timeout=10) as r: RESULT['novnc_internal']=b'noVNC' in r.read()
        if not RESULT['novnc_internal']: raise AssertionError('internal noVNC unavailable')
        RESULT['ok']=len(RESULT['cases'])==40 and all(x['ok'] for x in RESULT['cases']) and RESULT['restart_profile'] and RESULT['novnc_internal']
    except Exception as exc:
        RESULT['error']=type(exc).__name__; RESULT['error_detail']=str(exc)[:1500]
    finally:
        if stack is not None: stop_stack(stack)
        page_server.shutdown(); temp.cleanup()

def serve_result():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ('/','/health','/result'): self.send_response(404); self.end_headers(); return
            body=json.dumps(RESULT,separators=(',',':')).encode(); self.send_response(200 if RESULT.get('ok') else 503); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,*args): pass
    ThreadingHTTPServer(('0.0.0.0',RESULT_PORT),Handler).serve_forever()

if __name__=='__main__':
    run_cases(); print('ANTHARES_BROWSER_RENDER40_RESULT='+json.dumps(RESULT,separators=(',',':')),flush=True); serve_result()
