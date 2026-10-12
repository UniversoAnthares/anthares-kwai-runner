import json, os, pathlib, tempfile, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

MEDIA_URL=os.environ.get('MEDIA_URL','https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/x-full-flow-test-cache/anthares-x-e2e-38200942305.mp4')
PORT=int(os.environ.get('PORT','10000'))

class UploadPage(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'<!doctype html><input id="f" type="file"><div id="o"></div><script>f.onchange=()=>o.textContent=f.files[0].name+":"+f.files[0].size</script>'
        self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*a): pass

class App(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/health'):
            self.reply({'ok':True}); return
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
    def reply(self,obj):
        b=json.dumps(obj,separators=(',',':')).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

HTTPServer(('0.0.0.0',PORT),App).serve_forever()
