import json, os, pathlib, subprocess, threading, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import x_real_fullflow_once as x

ROOT=pathlib.Path('/app')
STATUS={'state':'booting','error':None,'result':None}

_original_discover=x.prep.discover_source

def discover_with_channel_fallback():
    try:
        return _original_discover()
    except Exception as exc:
        print('X_REAL_DISCOVERY_PRIMARY_FAIL='+type(exc).__name__+': '+str(exc),flush=True)
        # This ID was independently discovered from the public Universo Anthares channel page.
        return {
            'video_id':'xcRGdBfHX0E',
            'source_url':'https://www.youtube.com/watch?v=xcRGdBfHX0E',
            'title':'O Homem do Elevador',
            'duration':3012,
            'source_class':'long_form',
            'discovery_route':'channel-public-fallback'
        }

x.prep.discover_source=discover_with_channel_fallback

def corrected_render(scan,lo,hi,remove,out):
    keep=[]; cur=lo; edge=.03
    for r in remove:
        a=max(cur,r['start']-edge); b=min(hi,r['end']+edge)
        if a>cur+.03: keep.append((cur,a))
        cur=max(cur,b)
    if cur<hi-.03: keep.append((cur,hi))
    if not keep: raise RuntimeError('no useful interval')
    flt=[]; seq=[]
    for i,(a,b) in enumerate(keep):
        flt.append(f'[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]')
        flt.append(f'[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]')
        seq.append(f'[v{i}][a{i}]')
    flt.append(''.join(seq)+f'concat=n={len(keep)}:v=1:a=1[vcat][a]')
    flt.append('[vcat]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v]')
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(scan),
                    '-filter_complex',';'.join(flt),'-map','[v]','-map','[a]',
                    '-c:v','libx264','-preset','veryfast','-crf','20','-maxrate','3500k','-bufsize','7000k',
                    '-c:a','aac','-b:a','160k','-movflags','+faststart',str(out)],check=True,timeout=900)

x.render=corrected_render

def worker():
    STATUS['state']='running'
    try:
        rc=x.main()
        if rc not in (0,None): raise RuntimeError(f'pipeline returned {rc}')
        result=json.loads((ROOT/'x-render-result.json').read_text(encoding='utf-8'))
        STATUS.update(state='ready',result=result,error=None)
        print('X_REAL_RENDER_SERVICE_READY',flush=True)
    except Exception as exc:
        STATUS.update(state='failed',error=f'{type(exc).__name__}: {exc}')
        traceback.print_exc()

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/','/health','/status'):
            self.json({'ok':STATUS['state']!='failed',**STATUS}); return
        if self.path=='/result':
            p=ROOT/'x-render-result.json'
            if not p.exists(): self.json({'ok':False,'state':STATUS['state']},404); return
            data=p.read_bytes(); self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if self.path=='/media.mp4':
            p=ROOT/'x-cloud-output.mp4'
            if not p.exists(): self.json({'ok':False,'state':STATUS['state']},404); return
            size=p.stat().st_size; self.send_response(200); self.send_header('Content-Type','video/mp4'); self.send_header('Content-Length',str(size)); self.send_header('Cache-Control','public,max-age=3600'); self.end_headers()
            with p.open('rb') as f:
                while True:
                    b=f.read(1024*1024)
                    if not b: break
                    self.wfile.write(b)
            return
        self.send_response(404); self.end_headers()
    def json(self,obj,status=200):
        b=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*args): pass

threading.Thread(target=worker,daemon=True).start()
ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','10000'))),H).serve_forever()
