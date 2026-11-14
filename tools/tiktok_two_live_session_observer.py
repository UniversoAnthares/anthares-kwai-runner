#!/usr/bin/env python3
"""Read-only observer for two separate TikTok LIVE sessions.

Existing authenticated cookie state stays in RAM. Only hashed LIVE room IDs,
playback booleans and times are emitted. No RTMP keys, media URLs or bodies.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cortes_tiktok_lucasrosalem4_cloud_publish import state_from_secret

URL="https://www.tiktok.com/@lucasrosalem4/live"
DURATION=int(os.environ.get('LIVE_OBSERVER_SECONDS','470'))
INTERVAL=23
def h(value):
    return hashlib.sha256(str(value).encode()).hexdigest()[:16]
def candidates(text):
    found=[]
    for key in (r'(?:"room_id"|"roomId"|"roomID"|"webcast_room_id")\s*[:=]\s*["\']?(\d{12,25})',
                r'(?:room_id|roomId)=(\d{12,25})'):
        found.extend(re.findall(key,text or '',re.I))
    return list(dict.fromkeys(found))
def main():
    if not 90<=DURATION<=525:raise ValueError('OBSERVER_DURATION_UNSUPPORTED')
    state=state_from_secret()
    print('OBSERVER_AUTH_STATE=LOADED',flush=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--mute-audio','--autoplay-policy=no-user-gesture-required'])
        try:
            ctx=browser.new_context(storage_state=state,locale='pt-BR',viewport={'width':1440,'height':900})
            page=ctx.new_page()
            last_room=None; samples=0
            started=time.monotonic()
            while time.monotonic()-started < DURATION:
                tick=time.monotonic()
                observed=[]
                def request_cb(req):
                    try:
                        url=req.url
                        if 'tiktok.com' in url and ('webcast' in url or 'room' in url):
                            observed.extend(candidates(url))
                    except Exception: pass
                page.on('request',request_cb)
                try:
                    resp=page.goto(URL,wait_until='domcontentloaded',timeout=18000)
                    page.wait_for_timeout(3200)
                    html=page.content()[:700000]
                    observed.extend(candidates(html))
                    first=page.evaluate("""() => {
                       const v=document.querySelector('video[data-e2e], [data-e2e=live-room-content] video, video');
                       return {time:v?.currentTime||0,ready:v?.readyState||0,video:!!v,width:v?.videoWidth||0,height:v?.videoHeight||0,
                         audbytes:v?.webkitAudioDecodedByteCount||0,captured:v?.captureStream? v.captureStream().getAudioTracks().length:null};
                    }""")
                    page.wait_for_timeout(1800)
                    second=page.evaluate("() => document.querySelector('video')?.currentTime||0")
                    room=next((x for x in observed if len(x)>=12),None)
                    roomhash=h(room) if room else None
                    rec={'utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),'step':samples,
                         'http_ok':bool(resp and resp.status==200),'player':first['video'],
                         'ready':first['ready'],'advancing':bool(second>first['time']+0.4),
                         'dimensions':[first['width'],first['height']],
                         'audio_decoded':bool(first['audbytes']>0),
                         'audio_captured':first['captured'],'room_hash':roomhash,
                         'room_changed':bool(roomhash and last_room and roomhash!=last_room)}
                    if roomhash:last_room=roomhash
                    print('OBSERVATION='+json.dumps(rec,separators=(',',':')),flush=True)
                except Exception as e:
                    print('OBSERVATION_ERROR='+json.dumps({'utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),'type':type(e).__name__},separators=(',',':')),flush=True)
                finally:
                    try:page.remove_listener('request',request_cb)
                    except Exception:pass
                samples+=1
                delay=max(0,INTERVAL-(time.monotonic()-tick))
                time.sleep(delay)
            print('OBSERVER_FINISHED=1 samples='+str(samples),flush=True)
        finally:browser.close()
if __name__=='__main__':
    try: main()
    except Exception as e:
        print('OBSERVER_ERROR='+type(e).__name__,flush=True)
        sys.exit(1)
