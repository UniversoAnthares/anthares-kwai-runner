import json, os, pathlib, tempfile, threading, time, urllib.request, urllib.parse, subprocess, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

MEDIA_URL=os.environ.get('MEDIA_URL','https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/x-full-flow-test-cache/anthares-x-e2e-38200942305.mp4')
PORT=int(os.environ.get('PORT','10000'))
STORE=pathlib.Path('/tmp/anthares-xbench-media'); STORE.mkdir(parents=True,exist_ok=True)

class UploadPage(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'<!doctype html><input id="f" type="file"><div id="o"></div><script>f.onchange=()=>o.textContent=f.files[0].name+":"+f.files[0].size</script>'
        self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*a): pass

class App(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/transcode':
            self.send_response(404); self.end_headers(); return
        try:
            length=int(self.headers.get('content-length') or 0)
            body=json.loads(self.rfile.read(length) or b'{}')
            src=str(body.get('source_url') or '')
            if not src.startswith('https://'):
                raise RuntimeError('https source_url required')
            ident=uuid.uuid4().hex
            tmp=STORE/(ident+'.webm'); out=STORE/(ident+'.mp4')
            req=urllib.request.Request(src,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=120) as r, tmp.open('wb') as f:
                while True:
                    chunk=r.read(1024*1024)
                    if not chunk: break
                    f.write(chunk)
            if tmp.stat().st_size < 100_000:
                raise RuntimeError('source too small')
            subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(tmp),'-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','160k','-movflags','+faststart',str(out)],check=True,timeout=600)
            probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','json',str(out)],capture_output=True,text=True,check=True,timeout=30)
            meta=json.loads(probe.stdout or '{}')
            host=self.headers.get('host') or ''
            self.reply({'ok':True,'media_url':f'https://{host}/media/{ident}.mp4','bytes':out.stat().st_size,'probe':meta})
        except Exception as exc:
            self.reply({'ok':False,'error':f'{type(exc).__name__}: {exc}'},status=500)
    def do_GET(self):
        if self.path.startswith('/health'):
            self.reply({'ok':True,'ffmpeg':True}); return
        if self.path.startswith('/media/') and self.path.endswith('.mp4'):
            name=pathlib.Path(urllib.parse.urlparse(self.path).path).name
            path=STORE/name
            if not path.exists():
                self.send_response(404); self.end_headers(); return
            data=path.read_bytes(); self.send_response(200); self.send_header('Content-Type','video/mp4'); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','public,max-age=3600'); self.end_headers(); self.wfile.write(data); return
        if not self.path.startswith('/bench'):
            self.send_response(404); self.end_headers(); return
        t0=time.perf_counter(); tmp=pathlib.Path(tempfile.mkdtemp(prefix='render-xbench-')); mp4=tmp/'media.mp4'
        td=time.perf_counter(); urllib.request.urlretrieve(MEDIA_URL,mp4); download_s=time.perf_counter()-td; size=mp4.stat().st_size
        srv=HTTPServer(('127.0.0.1',0),UploadPage); threading.Thread(target=srv.serve_forever,daemon=True).start(); pport=srv.server_address[1]
        tl=time.perf_counter()
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
            launch_s=time.perf_counter()-tl; page=browser.new_page(); tn=time.perf_counter(); page.goto(f'http://127.0.0.1:{pport}',wait_until='domcontentloaded'); nav_s=time.perf_counter()-tn
            tu=time.perf_counter(); page.set_input_files('#f',str(mp4)); page.wait_for_function("document.querySelector('#f').files.length===1"); upload_s=time.perf_counter()-tu
            observed=page.locator('#f').evaluate('(e)=>({name:e.files[0].name,size:e.files[0].size})'); browser.close()
        srv.shutdown(); ok=(observed['name']=='media.mp4' and observed['size']==size)
        self.reply({'ok':ok,'bytes':size,'download_s':round(download_s,3),'launch_s':round(launch_s,3),'nav_s':round(nav_s,3),'upload_s':round(upload_s,3),'total_s':round(time.perf_counter()-t0,3)})
    def reply(self,obj,status=200):
        b=json.dumps(obj,separators=(',',':')).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

HTTPServer(('0.0.0.0',PORT),App).serve_forever()
