#!/usr/bin/env python3
"""Read-only evidence of TikTok's *ordinary* user LIVE controls, desktop/mobile.

Uses existing TikTok @lucasrosalem4 session and navigates only official pages.
Does not call undocumented APIs, create LIVE, attempt MFA bypass, or print secrets.
"""
from __future__ import annotations
import json
import sys
from playwright.sync_api import sync_playwright
from tiktok_live_account_access_probe import state_from_secret

CASES = (
    ("desktop-profile", "desktop", "https://www.tiktok.com/@lucasrosalem4"),
    ("desktop-live-creator", "desktop", "https://www.tiktok.com/live/creator"),
    ("desktop-producer", "desktop", "https://livecenter.tiktok.com/producer"),
    ("mobile-profile", "mobile", "https://www.tiktok.com/@lucasrosalem4"),
    ("mobile-live-creator", "mobile", "https://www.tiktok.com/live/creator"),
)
SCRIPT = """() => {
  const isVisible=e=>{const b=e.getBoundingClientRect();const s=getComputedStyle(e);return b.width>0&&b.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
  const body=(document.body?.innerText||'').toLowerCase().slice(0,40000);
  const controls=[...document.querySelectorAll('button,a,[role="button"],[role="menuitem"]')]
    .filter(isVisible).slice(0,320)
    .map(e=>({label:(e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim().toLowerCase().slice(0,150), disabled:!!e.disabled||e.getAttribute('aria-disabled')==='true'}));
  const direct=controls.filter(x=>/^(go live|iniciar live|iniciar ao vivo|fazer live|transmitir ao vivo|go live now)$/.test(x.label));
  const create=controls.filter(x=>/^(criar|create|\\+|fazer live)/.test(x.label)).length;
  return {
     go_live_control:direct.length>0,
     go_live_enabled:direct.some(x=>!x.disabled),
     create_controls:create,
     rtmp_control:controls.some(x=>/stream key|chave de transmiss|rtmp/.test(x.label)),
     login_form:!!document.querySelector('input[type="password"]'),
     login_words:/^(entrar|log in|sign in)$/.test((document.querySelector('button')?.innerText||'').toLowerCase().trim()),
     studio_download:controls.some(x=>/baixe o live studio|download live studio/.test(x.label)),
     live_label:body.includes('live'),
     account_marker:body.includes('lucasrosalem4')
  };
}"""

def main():
    state = state_from_secret()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            contexts = {
                "desktop": browser.new_context(storage_state=state, locale="pt-BR",
                                               viewport={"width":1440, "height":900}),
                "mobile": browser.new_context(storage_state=state, locale="pt-BR",
                                              **p.devices["iPhone 13"])
            }
            try:
                for name, device, url in CASES:
                    page=contexts[device].new_page()
                    try:
                        response=page.goto(url, wait_until="domcontentloaded", timeout=40000)
                        page.wait_for_timeout(3500)
                        result=page.evaluate(SCRIPT)
                        result.update({"stage":name,"http":response.status if response else 0})
                        if result["http"] in (401,403,429):
                            result["status"]="AUTH_OR_QUOTA_STOP"
                            print("TIKTOK_STANDARD_UI="+json.dumps(result,sort_keys=True),flush=True)
                            continue
                        result["status"]="VISIBLE_GO_LIVE" if result["go_live_enabled"] else "NO_VISIBLE_GO_LIVE"
                        print("TIKTOK_STANDARD_UI="+json.dumps(result,sort_keys=True),flush=True)
                    except Exception as exc:
                        print("TIKTOK_STANDARD_UI="+json.dumps({"stage":name,"status":"NAVIGATION_OR_DOM_ERROR",
                          "kind":type(exc).__name__},sort_keys=True),flush=True)
                    finally:
                        page.close()
            finally:
                for context in contexts.values():context.close()
        finally:
            browser.close()
    print("TIKTOK_STANDARD_UI_READONLY_COMPLETE=1",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("TIKTOK_STANDARD_UI_PROBE_STOP="+type(exc).__name__.upper(),flush=True)
        sys.exit(1)
