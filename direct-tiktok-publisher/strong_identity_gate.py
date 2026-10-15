#!/usr/bin/env python3
"""Fail-closed TikTok identity gate bound to the canonical Anthares Browser session."""
import json
import os
import re
import time
from playwright.sync_api import sync_playwright
import tiktok_worker as tw
from tiktok_session_authority import load_canonical_state


def main():
    expected=os.environ.get("EXPECTED_TIKTOK_USERNAME","").strip().lstrip("@").casefold()
    if not expected or expected!="universo.anthares":
        raise RuntimeError("unexpected TikTok account")

    state,authority=load_canonical_state()
    tw.STORAGE_RAW=json.dumps(state,separators=(",",":"))
    tw.STORAGE_FILE=""
    tw.EXPECTED_USERNAME="universo.anthares"
    print(
        "TIKTOK_IDENTITY_AUTHORITY=runtime sha256="+authority["ciphertext_sha256"]
        +" cookies="+str(authority["cookie_count"]),
        flush=True,
    )

    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--disable-dev-shm-usage","--no-sandbox","--disable-gpu"])
        context=browser.new_context(storage_state=state,viewport={"width":1440,"height":1000},locale="pt-BR")
        try:
            page=context.new_page()
            page.goto("https://www.tiktok.com/foryou",wait_until="domcontentloaded",timeout=60000)
            time.sleep(5)
            tw.validate_tiktok_session(page,context)
            try:
                page.goto("https://www.tiktok.com/profile",wait_until="domcontentloaded",timeout=30000)
                time.sleep(2)
                m=re.search(r"/@([^/?#]+)",page.url,re.I)
                if m and m.group(1).casefold()!=expected:
                    raise RuntimeError("TikTok /profile belongs to a different account")
                print("TIKTOK_PROFILE_REDIRECT="+("matched" if m else "not_available"),flush=True)
            except RuntimeError:
                raise
            except Exception as exc:
                print("TIKTOK_PROFILE_REDIRECT=unavailable_"+type(exc).__name__,flush=True)
            print("TIKTOK_IDENTITY_GATE=PROVEN account="+expected,flush=True)
        finally:
            context.close()
            browser.close()

if __name__=="__main__":
    main()
