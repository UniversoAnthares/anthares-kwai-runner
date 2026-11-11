#!/usr/bin/env python3
"""Read-only TikTok LIVE desktop availability. Never starts or changes LIVE.

Reuses the account's existing sealed Playwright storage state supplied via an
Actions secret. Reports only booleans and normalized destination, no identity,
cookies, authentication tokens, screenshots, or source pages in logs.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parent))
from cortes_tiktok_lucasrosalem4_cloud_publish import state_from_secret

PAGES=[
    ("creator_studio","https://www.tiktok.com/tiktokstudio"),
    ("live_producer","https://livecenter.tiktok.com/producer"),
    ("live_center","https://livecenter.tiktok.com/"),
    ("creator_live","https://www.tiktok.com/tiktokstudio/live"),
    ("seller_center","https://seller-br.tiktok.com/"),
    ("public_live","https://www.tiktok.com/@lucasrosalem4/live"),
]
MARKERS={
  "browser_go_live": ["go live","fazer live","iniciar live","transmitir ao vivo"],
  "virtual_camera": ["virtual camera","câmera virtual","camera source","fonte de vídeo"],
  "practice_mode": ["practice mode","modo de prática"],
  "shop_manager": ["gerenciador de live","live manager","live & video","live e vídeo"]
}

def inspect(page,response,label):
    url=urlsplit(page.url)
    host=(url.hostname or "").lower()
    current_path=url.path[:110]
    body=page.locator("body").inner_text(timeout=4500).lower()[:15000]
    password=page.locator('input[type="password"]').count()>0
    login_route="/login" in url.path.lower() or "login" in host
    login_prompt=any(t in body[:1000] for t in ("log in to tiktok","entrar no tiktok","faça login para"))
    controls=page.locator("button,a,[role=button]").evaluate_all("""els=>els.filter(e=>{
      const r=e.getBoundingClientRect();return r.width>0 && r.height>0
    }).map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim().toLowerCase()).slice(0,350)""")
    return {
       "name":label,
       "http_ok":bool(response and 200<=response.status<400),
       "tiktok_owned_domain": host=="tiktok.com" or host.endswith(".tiktok.com"),
       "redirect_to_login":login_route,
       "login_ui":password or login_prompt,
       "route":current_path,
       "visible_text_length":len(body),
       "visible_control_count":len(controls),
       "document_title_length":len(page.title()),
       "studio_download_hint":any(k in body for k in ("live studio","baixar o live studio","download live studio")),
       "shop_access_hint":any(k in body for k in ("seller center","central do vendedor","seller login","portal do vendedor")),
       "login_button_hint":any(k in c for c in controls for k in ("log in","sign in","entrar","cadastre-se")),
       "js_root_present":page.locator("#root,#app,#__next").count()>0,
       "browser_go_live_control": any(any(k in c for k in MARKERS["browser_go_live"]) for c in controls),
       "browser_camera_control":any(any(k in c for k in MARKERS["virtual_camera"]) for c in controls),
       "shop_live_manager_control":any(any(k in c for k in MARKERS["shop_manager"]) for c in controls),
       "practice_hint":any(k in body for k in MARKERS["practice_mode"]),
       "generic_go_live_text":any(k in body for k in MARKERS["browser_go_live"]),
       "iframe_count":min(10,page.locator("iframe").count()),
    }

def main():
    try:
        state=state_from_secret()
    except Exception as exc:
        print("NATIVE_TIKTOK_EXISTING_SESSION="+type(exc).__name__,flush=True)
        return 0
    # The cookie jar is loaded in-memory. Storage is never saved to disk or re-exported.
    print("NATIVE_TIKTOK_EXISTING_STATE_LOADED=1",flush=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="chrome",headless=True,args=["--no-sandbox","--disable-dev-shm-usage",
                                    "--use-fake-device-for-media-stream",
                                    "--use-fake-ui-for-media-stream"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR",
                                    permissions=["camera","microphone"],
                                    viewport={"width":1440,"height":900})
            page=ctx.new_page()
            results=[]
            for name,url in PAGES:
                try:
                    r=page.goto(url,wait_until="domcontentloaded",timeout=28000)
                    page.wait_for_timeout(3500)
                    result=inspect(page,r,name)
                    if name=="public_live":
                        # Only rendered media and visible labels; never record stream URLs,
                        # cookies, tokens or the page's content.
                        js="""() => {
                          const visible = e => {
                            const r=e.getBoundingClientRect(),s=getComputedStyle(e);
                            return r.width>0 && r.height>0 && s.display!=='none' && s.visibility!=='hidden';
                          };
                          const video=[...document.querySelectorAll('video')].filter(visible)[0];
                          const labels=(document.body?.innerText||'').slice(0,6000).toLowerCase();
                          return {media_visible:!!video,ready_state:video?.readyState||0,
                            time:video&&Number.isFinite(video.currentTime)?video.currentTime:0,
                            paused:video?.paused!==false,has_source:!!(video&&(video.currentSrc||video.src)),
                            source_object:!!video?.srcObject,
                            audio_tracks:video?.srcObject?.getAudioTracks?.()?.length??0,
                            audio_track_live:video?.srcObject?.getAudioTracks?.()?.some(x=>x.readyState==='live'&&!x.muted)??false,
                            video_tracks:video?.srcObject?.getVideoTracks?.()?.length??0,
                            muted:video?.muted??true,volume:video?.volume??0,
                            width:video?.videoWidth||0,height:video?.videoHeight||0,
                            duration:Number.isFinite(video?.duration)?Math.round(video.duration):null,
                            media_count:document.querySelectorAll('video').length,
                            player_e2e:video?.closest('[data-e2e]')?.getAttribute('data-e2e')||null,
                            visible_live_label:/\b(live|ao vivo)\b/.test(labels),
                            visible_offline_label:/\b(not live|offline|ended|indisponível|transmissão encerrada)\b/.test(labels)};
                        }"""
                        before=page.evaluate(js)
                        page.wait_for_timeout(4200)
                        after=page.evaluate(js)
                        result["public_media_visible"]=bool(after["media_visible"])
                        result["public_media_ready"]=bool(after["ready_state"]>=2)
                        result["public_media_playback_advancing"]=bool(after["time"]>before["time"]+0.5)
                        result["public_media_paused"]=bool(after["paused"])
                        result["public_media_has_source"]=bool(after["has_source"])
                        result["public_media_source_object"]=bool(after["source_object"])
                        result["public_audio_tracks"]=int(after["audio_tracks"])
                        result["public_audio_track_live"]=bool(after["audio_track_live"])
                        result["public_video_tracks"]=int(after["video_tracks"])
                        result["public_player_muted"]=bool(after["muted"])
                        result["public_player_volume"]=float(after["volume"])
                        result["public_media_dimensions"]=[int(after["width"]),int(after["height"])]
                        result["public_media_duration"]=after["duration"]
                        result["public_video_elements"]=int(after["media_count"])
                        result["public_player_e2e"]=after["player_e2e"]
                        result["public_live_label"]=bool(after["visible_live_label"])
                        result["public_offline_label"]=bool(after["visible_offline_label"])
                        result["public_observation"]="playing" if result["public_media_ready"] and result["public_media_playback_advancing"] else ("login_required" if result["redirect_to_login"] or result["login_ui"] else "unconfirmed")
                    results.append(result)
                except Exception as exc:
                    results.append({"name":name,"navigation_error":type(exc).__name__})
            print("NATIVE_TIKTOK_BROWSER_PROBE="+json.dumps({"results":results},
                  ensure_ascii=False,separators=(",",":")),flush=True)
        finally:
            browser.close()
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("NATIVE_TIKTOK_BROWSER_FAILURE="+type(exc).__name__,flush=True)
        sys.exit(1)
