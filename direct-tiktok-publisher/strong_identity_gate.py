#!/usr/bin/env python3
"""Fail-closed TikTok identity gate shared by the real one-shot workflow.

Hydration can be absent on TikTok Studio even when an authenticated
profile session is valid. Do not mistake missing hydration for a mismatch.
Require authentication cookies, no login gate, and a positive account
match from the existing multi-signal session validator. Reject any
explicitly observed different /profile owner.
"""
import json
import os
import re
import time
from playwright.sync_api import sync_playwright
import tiktok_worker as tw

def main():
    expected=os.environ.get("EXPECTED_TIKTOK_USERNAME","").strip().lstrip("@").casefold()
    if not expected or expected!="universo.anthares":
        raise RuntimeError("unexpected TikTok account")
    state=tw.storage_state()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--disable-dev-shm-usage","--no-sandbox","--disable-gpu"])
        context=browser.new_context(storage_state=state,viewport={"width":1440,"height":1000},locale="pt-BR")
        try:
            page=context.new_page()
            page.goto("https://www.tiktok.com/foryou",wait_until="domcontentloaded",timeout=60000)
            time.sleep(5)
            # Existing validator checks authenticated cookies, challenge,
            # visible login gates and the expected account across several views.
            tw.validate_tiktok_session(page,context)
            # Explicit contradictory evidence must veto publication.
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
