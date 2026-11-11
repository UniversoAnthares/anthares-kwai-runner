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
    ("live_center","https://livecenter.tiktok.com/"),
    ("seller_center","https://seller-br.tiktok.com/"),
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
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage",
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
                    page.wait_for_timeout(3200)
                    results.append(inspect(page,r,name))
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
