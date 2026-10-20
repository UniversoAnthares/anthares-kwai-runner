#!/usr/bin/env python3
"""Read-only TikTok upload surface diagnostic. Never chooses media or posts."""
from __future__ import annotations
import json
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
    return {
        "on_owned_tiktok_domain":site in ("www.tiktok.com","tiktok.com"),
        "file_input_present":inputs>0,
        "file_input_count":min(inputs,10),
        "login_gate":bool(page.locator('input[type="password"]').count()) or "/login" in page.url,
        "captcha_or_security_gate":bool(re.search(r"captcha|verify to continue|security check|verifica[cç][aã]o de seguran[cç]a",body)),
        "studio_route":"/tiktokstudio/" in page.url,
        "redirected_to_profile":"/@" in page.url,
        "upload_route":"/upload" in page.url,
    }

def main():
    state,_=load_canonical_state()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            context=browser.new_context(storage_state=state,locale="pt-BR",viewport={"width":1440,"height":900})
            page=context.new_page()
            out=[]
            for i,url in enumerate(urls,1):
                try:
                    page.goto(url,wait_until="domcontentloaded",timeout=38000)
                    page.wait_for_timeout(1200)
                    d=inspect(page); d["candidate"]=i;d["navigation"]="ok"
                    out.append(d)
                    if d["file_input_present"] and not d["login_gate"] and not d["captcha_or_security_gate"]:
                        break
                except Exception as exc:
                    out.append({"candidate":i,"navigation":"failed","exception_type":type(exc).__name__})
            result={"checks":out,"ready_to_accept_file":any(
                d.get("file_input_present") and not d.get("login_gate") and not d.get("captcha_or_security_gate")
                for d in out)}
            print("CORTES_TIKTOK_READONLY_UPLOAD_DIAGNOSTIC="+json.dumps(result,sort_keys=True,separators=(",",":")),flush=True)
            return 0
        finally:browser.close()

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("CORTES_TIKTOK_READONLY_EXCEPTION="+type(exc).__name__,flush=True)
        sys.exit(2)
