#!/usr/bin/env python3
"""Read-only TikTok upload surface diagnostic. Never chooses media or posts."""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"direct-tiktok-publisher"))
from tiktok_session_authority import load_canonical_state
from playwright.sync_api import sync_playwright

urls=("https://www.tiktok.com/tiktokstudio/upload?from=webapp",
      "https://www.tiktok.com/upload?lang=pt-BR")

def inspect(page):
    body=(page.locator("body").inner_text(timeout=2500) or "").lower()
    site=page.url.split("/")[2] if "://" in page.url else ""
    inputs=page.locator('input[type="file"]').count()
    framed=0
    for frame in page.frames[1:]:
        try: framed+=frame.locator('input[type="file"]').count()
        except Exception: pass
    return {
        "on_owned_tiktok_domain":site in ("www.tiktok.com","tiktok.com"),
        "file_input_present":inputs>0,
        "file_input_count":min(inputs,10),
        "iframe_file_input_count":min(framed,10),
        "iframe_count":min(len(page.frames)-1,12),
        "body_text_size":min(len(body),30000),
        "app_dom_found":page.locator("#root,#app,#__next").count()>0,
        "upload_control_hints":bool(re.search(r"select video|selecionar v[ií]deo|carregar v[ií]deo|upload video|choose file",body)),
        "unavailable_page_hint":bool(re.search(r"not available|access denied|unavailable|forbidden|something went wrong|try again later",body)),
        "login_gate":bool(page.locator('input[type="password"]').count()) or "/login" in page.url,
        "captcha_or_security_gate":bool(re.search(r"captcha|verify to continue|security check|verifica[cç][aã]o de seguran[cç]a",body)),
        "studio_route":"/tiktokstudio/" in page.url,
        "redirected_to_profile":"/@" in page.url,
        "upload_route":"/upload" in page.url,
    }

def main():
    state,_=load_canonical_state()
    with sync_playwright() as p:
        headful=os.getenv("TIKTOK_PROBE_HEADFUL","0")=="1"
        browser=p.chromium.launch(headless=not headful,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            context=browser.new_context(storage_state=state,locale="pt-BR",viewport={"width":1440,"height":900})
            page=context.new_page()
            out=[]
            for i,url in enumerate(urls,1):
                try:
                    response=page.goto(url,wait_until="domcontentloaded",timeout=38000)
                    page.wait_for_timeout(8500)
                    d=inspect(page); d["candidate"]=i;d["navigation"]="ok"
                    d["http_error"]=bool(response and response.status>=400)
                    out.append(d)
                    if d["file_input_present"] and not d["login_gate"] and not d["captcha_or_security_gate"]:
                        break
                except Exception as exc:
                    out.append({"candidate":i,"navigation":"failed","exception_type":type(exc).__name__})
            result={"checks":out,"ready_to_accept_file":any(
                (d.get("file_input_present") or d.get("iframe_file_input_count")) and not d.get("login_gate") and not d.get("captcha_or_security_gate")
                for d in out)}
            result["headful"]=headful
            print("CORTES_TIKTOK_READONLY_UPLOAD_DIAGNOSTIC="+json.dumps(result,sort_keys=True,separators=(",",":")),flush=True)
            return 0
        finally:browser.close()

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("CORTES_TIKTOK_READONLY_EXCEPTION="+type(exc).__name__,flush=True)
        sys.exit(2)
