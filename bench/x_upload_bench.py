import json, os, pathlib, subprocess, sys, tempfile, time, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

MEDIA_URL=os.environ.get('MEDIA_URL','https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/x-full-flow-test-cache/anthares-x-e2e-38200942305.mp4')
RUN_LABEL=os.environ.get('RUN_LABEL','local')

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'<!doctype html><html><body><input id="f" type="file"><div id="out"></div><script>document.querySelector("#f").addEventListener("change",e=>{const f=e.target.files[0];document.querySelector("#out").textContent=f?f.name+":"+f.size:"none"})</script></body></html>'
        self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*a): pass

def main():
    t0=time.perf_counter(); tmp=pathlib.Path(tempfile.mkdtemp(prefix='xbench-')); mp4=tmp/'media.mp4'
    td=time.perf_counter(); urllib.request.urlretrieve(MEDIA_URL, mp4); download_s=time.perf_counter()-td
    size=mp4.stat().st_size
    srv=HTTPServer(('127.0.0.1',0),H); Thread(target=srv.serve_forever,daemon=True).start(); port=srv.server_address[1]
    from playwright.sync_api import sync_playwright
    tl=time.perf_counter()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        launch_s=time.perf_counter()-tl
        page=browser.new_page()
        tn=time.perf_counter(); page.goto(f'http://127.0.0.1:{port}',wait_until='domcontentloaded'); nav_s=time.perf_counter()-tn
        tu=time.perf_counter(); page.set_input_files('#f',str(mp4)); page.wait_for_function("document.querySelector('#f').files.length===1"); upload_s=time.perf_counter()-tu
        observed=page.locator('#f').evaluate('(e)=>({name:e.files[0].name,size:e.files[0].size})')
        browser.close()
    srv.shutdown()
    ok=(observed['size']==size and observed['name']=='media.mp4')
    out={'label':RUN_LABEL,'ok':ok,'bytes':size,'download_s':round(download_s,3),'launch_s':round(launch_s,3),'nav_s':round(nav_s,3),'upload_s':round(upload_s,3),'total_s':round(time.perf_counter()-t0,3)}
    print(json.dumps(out,separators=(',',':')))
    pathlib.Path('bench-result.json').write_text(json.dumps(out,indent=2))
    raise SystemExit(0 if ok else 2)
if __name__=='__main__': main()
