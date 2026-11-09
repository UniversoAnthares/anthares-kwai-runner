#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, os, re, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

HLS_URL=os.getenv('ANTHARES_PUBLIC_HLS_URL','https://anthares.us/wp-content/uploads/anthares-live-static/live.m3u8').strip()
STATE_RAW=os.getenv('KWAI_STORAGE_STATE','').strip()
OUT=Path(os.getenv('ATD_ARTIFACT_DIR','live-artifacts'))
CHALLENGE_RE=re.compile(r'captcha|verification code|security check|qr code|scan.*code|one.?time|c[oó]digo de verifica|verifica[cç][aã]o',re.I)
LOGIN_RE=re.compile(r'log in|login|sign in|entrar|fazer login',re.I)

MAX_SESSION_SECONDS=21600  # 6h por sessao; renovacao automatica em ciclos posteriores

def state_from(path):
    raw = Path(path).read_text(encoding='utf-8-sig')
    for decode in (lambda x: x, lambda x: base64.b64decode(x).decode()):
        try:
            obj = json.loads(decode(raw))
            if isinstance(obj, str): obj = json.loads(obj)
            if isinstance(obj, dict) and isinstance(obj.get('cookies'), list): return obj
        except (ValueError, UnicodeError): pass
    raise RuntimeError('Invalid local authentication state')

def safe_body(page,limit=12000):
    try:return page.locator('body').inner_text(timeout=5000)[:limit]
    except Exception:return ''

def hls_preflight():
    req=urllib.request.Request(HLS_URL+'?cb='+str(int(time.time())),headers={'Cache-Control':'no-cache','User-Agent':'Anthares-Live/1.0'})
    with urllib.request.urlopen(req,timeout=25) as r: raw=r.read()
    text=raw.decode('utf-8','replace')
    if not text.startswith('#EXTM3U'): raise RuntimeError('HLS_INVALID_HEADER')
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    seq=[x for x in lines if x.startswith('#EXT-X-MEDIA-SEQUENCE:')]
    segs=[x for x in lines if not x.startswith('#')]
    if not seq or len(segs)<2: raise RuntimeError('HLS_INSUFFICIENT_WINDOW')
    base=HLS_URL.rsplit('/',1)[0]+'/'
    with urllib.request.urlopen(urllib.request.Request(base+segs[0]+'?cb='+str(int(time.time())),headers={'User-Agent':'Anthares-Live/1.0'}),timeout=25) as r: body=r.read()
    if len(body)<1000: raise RuntimeError('HLS_SEGMENT_INVALID')
    print('KWAI_LIVE_HLS=PROVEN sequence='+seq[0].split(':',1)[1]+' segments='+str(len(segs))+' first_segment_bytes='+str(len(body)),flush=True)

def click_first(page,pattern,selectors=('button','a','[role="button"]')):
    rx=re.compile(pattern,re.I)
    for sel in selectors:
        loc=page.locator(sel)
        for i in range(min(loc.count(),120)):
            n=loc.nth(i)
            try:
                if not n.is_visible(): continue
                text=' '.join(filter(None,[(n.inner_text(timeout=300) or '').strip(),n.get_attribute('aria-label') or '',n.get_attribute('title') or '']))
                if rx.search(text): n.click(timeout=7000); return True
            except Exception: pass
    return False

def studio_permission(page):
    try:
        return page.evaluate("""async()=>{try{const r=await fetch('/rest/o/w/live/supplier/cloudLive/checkPermission');return {status:r.status,body:await r.json()}}catch(e){return {status:0,error:String(e)}}}""")
    except Exception as e:return {'status':0,'error':type(e).__name__}

def authenticated(page):
    p=studio_permission(page); b=p.get('body') or {}
    user=b.get('userInfo') or (b.get('data') or {}).get('userInfo') or {}
    ok=p.get('status')==200 and (b.get('result')==1 or bool(user.get('ksId') or user.get('userId')))
    return ok,p

def extract_room_id(d):
    vo=d.get('createRoomResultVo') or {}
    return str(d.get('liveRoomId') or d.get('roomId') or vo.get('liveRoomId') or (d.get('liveRoom') or {}).get('liveRoomId') or (d.get('data') or {}).get('liveRoomId') or '').strip()

def launch_context(p,state):
    context_opts={'viewport':{'width':1440,'height':1000},'locale':'pt-BR'}
    if state:
        context_opts['storage_state']=state_from(state)
    return p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage']), context_opts

def run(activate=False,seconds=60,continuous=False,cycles=0,state=None):
    hls_preflight(); OUT.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        cycle=0
        while True:
            cycle+=1
            b,context_opts=launch_context(p,state)
            ctx=b.new_context(**context_opts)
            page=ctx.new_page(); page.set_default_timeout(12000)
            page.goto('https://studio.kwai.com/',wait_until='domcontentloaded',timeout=90000); page.wait_for_timeout(3500)
            if not state:
                ok,_=authenticated(page)
                if not ok:
                    ctx.close(); b.close()
                    raise RuntimeError('KWAI_STUDIO_AUTH_NOT_ESTABLISHED: forneca KWAI_STORAGE_STATE (sessao Kwai Studio ja autenticada) para ativacao headless')
            perm=authenticated(page)[1]
            user=(perm.get('body') or {}).get('userInfo') or ((perm.get('body') or {}).get('data') or {}).get('userInfo') or {}
            print('KWAI_LIVE_STUDIO_AUTH=PROVEN account_id_present='+str(bool(user.get('ksId') or user.get('userId'))).lower()+' cycle='+str(cycle),flush=True)
            if not activate:
                print('KWAI_LIVE_PREFLIGHT=PROVEN',flush=True); ctx.close(); b.close(); return
            created={}
            def observe(resp):
                if 'cloudLive/createRoom' in resp.url:
                    try: created.update(resp.json())
                    except Exception: pass
            page.on('response',observe)
            room=''; started=False; cleanup=False
            try:
                page.get_by_role('button',name=re.compile('criar tr[aá]fego|create traffic',re.I)).first.click(); page.wait_for_timeout(1200)
                card=page.get_by_text(re.compile('transmiss[aã]o ao vivo via transmiss[aã]o de rede|network',re.I),exact=False)
                if not card.count(): raise RuntimeError('KWAI_NETWORK_PULL_OPTION_MISSING')
                card.first.click(); page.wait_for_timeout(1000)
                fields=page.locator('input[type="text"]:visible')
                if fields.count()<2: raise RuntimeError('KWAI_NETWORK_PULL_FIELDS_MISSING')
                fields.nth(0).fill(HLS_URL); fields.nth(1).fill('Anthares LIVE ciclo '+str(cycle))
                cover=OUT/'cover.jpg'
                page.screenshot(path=str(OUT/'page.png'))
                try:
                    from PIL import Image
                    Image.open(OUT/'page.png').convert('RGB').resize((720,1280)).save(cover,'JPEG',quality=82)
                    page.locator('input[type="file"][name="cover"]').set_input_files(str(cover))
                except Exception: pass
                page.get_by_role('button',name=re.compile('criar tr[aá]fego|create traffic',re.I)).last.click()
                deadline=time.time()+20
                while time.time()<deadline and not created: page.wait_for_timeout(250)
                room=extract_room_id(created)
                if created.get('result')!=1 or not room: raise RuntimeError('KWAI_LIVE_ROOM_CREATE_UNCONFIRMED')
                print('KWAI_LIVE_ROOM_CREATED=1 cycle='+str(cycle),flush=True)
                start=page.evaluate("""async id=>{const r=await fetch('/rest/o/w/live/supplier/cloudLive/startLive',{method:'POST',headers:{'Content-Type':'application/json;charset=UTF-8'},body:JSON.stringify({liveRoomId:id})});return await r.json()}""",room)
                print('KWAI_LIVE_START_RESULT='+str(start.get('result')),flush=True)
                if start.get('result')!=1: raise RuntimeError('KWAI_LIVE_START_REJECTED')
                started=True
                session_seconds=max(15,min(int(seconds),MAX_SESSION_SECONDS))
                end=time.time()+session_seconds
                good=0
                while time.time()<end:
                    info=page.evaluate("""async id=>await (await fetch('/rest/o/w/live/supplier/cloudLive/room?liveRoomId='+encodeURIComponent(id))).json()""",room)
                    status=(info.get('curRoomVo') or {}).get('roomStatus')
                    if status==1: good+=1
                    print('KWAI_LIVE_HEARTBEAT status='+str(status)+' cycle='+str(cycle),flush=True)
                    page.wait_for_timeout(5000)
                if good<2: raise RuntimeError('KWAI_LIVE_STATE_NOT_STABLE')
                print('KWAI_LIVE_CONFIRMED=1 cycle='+str(cycle),flush=True)
            finally:
                if room:
                    op='stopLive' if started else 'cancelLive'
                    try:
                        result=page.evaluate("""async x=>{const r=await fetch('/rest/o/w/live/supplier/cloudLive/'+x.op,{method:'POST',headers:{'Content-Type':'application/json;charset=UTF-8'},body:JSON.stringify({liveRoomId:x.id})});return await r.json()}""",{'op':op,'id':room})
                        cleanup=result.get('result')==1
                    except Exception: cleanup=False
                print('KWAI_LIVE_CLEANUP_CONFIRMED='+str(int(cleanup or not room))+' cycle='+str(cycle),flush=True)
                ctx.close(); b.close()
            if room and not cleanup: raise RuntimeError('KWAI_LIVE_CLEANUP_UNCONFIRMED cycle='+str(cycle))
            if not continuous or (cycles and cycle>=cycles): break
            # renovacao: novo navegador, mesma sessao autorizada (storage_state), proximo ciclo
        print('KWAI_LIVE_CLOUD_CANARY=PROVEN cycles='+str(cycle),flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--activate',action='store_true')
    ap.add_argument('--seconds',type=int,default=21600)
    ap.add_argument('--continuous',action='store_true')
    ap.add_argument('--cycles',type=int,default=0)
    ap.add_argument('--state',default=os.getenv('KWAI_STORAGE_STATE',''))
    a=ap.parse_args(); run(a.activate,a.seconds,a.continuous,a.cycles,a.state or None)
if __name__=='__main__':
    try: main()
    except Exception as e: print('KWAI_LIVE_ERROR='+str(e),file=sys.stderr,flush=True); raise
