#!/usr/bin/env python3
"""Read-only TikTok LIVE eligibility diagnostic on an ephemeral GitHub runner.

Uses the existing compressed owner-authorized TikTok storage-state secret.
No stream keys, cookies, profile writes, uploads, LIVE creation, or login bypass.
Reports only booleans and bounded status codes; all browser resources are closed.
"""
from __future__ import annotations
import base64
import json
import os
import re
import sys
import time
import zlib
from urllib.parse import urlsplit

EXPECTED = "lucasrosalem4"

def state_from_secret():
    raw = os.getenv("TIKTOK_LUCASROSALEM4_STORAGE_STATE", "")
    if not raw or len(raw) > 48000:
        raise ValueError("CLOUD_SESSION_SECRET_MISSING_OR_TOO_LARGE")
    try:
        decoder = zlib.decompressobj()
        data = decoder.decompress(base64.b64decode(raw, validate=True), 600001)
        if not decoder.eof:
            raise ValueError("CLOUD_SESSION_COMPRESSION_INCOMPLETE")
    except Exception as exc:
        raise ValueError("CLOUD_SESSION_FORMAT_UNSUPPORTED") from exc
    if len(data) > 600000:
        raise ValueError("CLOUD_SESSION_TOO_LARGE")
    try:
        state = json.loads(data)
    except (ValueError, TypeError) as exc:
        raise ValueError("CLOUD_SESSION_NOT_JSON") from exc
    if not isinstance(state, dict) or not isinstance(state.get("cookies"), list):
        raise ValueError("CLOUD_SESSION_NOT_PLAYWRIGHT_STATE")
    auth = [
        c for c in state["cookies"]
        if c.get("name") in ("sessionid", "sessionid_ss", "sid_tt")
        and "tiktok.com" in str(c.get("domain", ""))
        and (float(c.get("expires") or 0) <= 0 or float(c["expires"]) > time.time())
    ]
    if not auth:
        raise ValueError("CLOUD_SESSION_AUTH_COOKIES_EXPIRED")
    return state

def inspect(page, stage):
    from playwright.sync_api import TimeoutError as BrowserTimeoutError
    url = ("https://www.tiktok.com/tiktokstudio/content" if stage == "studio"
           else "https://livecenter.tiktok.com/producer")
    status = 0
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        status = resp.status if resp else 0
        page.wait_for_timeout(3500)
    except BrowserTimeoutError:
        return {"stage": stage, "status": status, "outcome": "PAGE_TIMEOUT"}
    except Exception:
        return {"stage": stage, "status": status, "outcome": "PAGE_NAVIGATION_ERROR"}

    # Only bounded boolean evidence is exported. Avoid page text, URL queries,
    # cookies, authenticated requests, screenshots, and sensitive DOM details.
    signal = page.evaluate("""() => {
      const text=(document.body?.innerText||'').toLowerCase().slice(0,45000);
      const labels=[...document.querySelectorAll('button,a,[role=button]')]
        .filter(x=>{const b=x.getBoundingClientRect();return b.width>0&&b.height>0})
        .map(x=>(x.innerText||x.getAttribute('aria-label')||'').toLowerCase().trim()).slice(0,180);
      const links=[...document.querySelectorAll('a[href]')].map(x=>x.getAttribute('href')||'');
      const login=!!document.querySelector('input[type=password]')
           || /(?:sign in|log in|fazer login|entrar na conta)/i.test(text.slice(0,2500));
      const actions=labels.filter(s=>/rtmp|stream key|chave de transmiss|software|obs|go live|iniciar live|transmitir ao vivo/.test(s));
      return {
        login_prompt:login,
        owner_media_links:links.some(s=>s.toLowerCase().includes('/@lucasrosalem4/video/')),
        owner_marker:text.includes('lucasrosalem4'),
        producer_marker:text.includes('live center')||text.includes('central de live')||text.includes('live studio'),
        rtmp_label_visible:actions.some(s=>/rtmp|stream key|chave de transmiss/.test(s)),
        live_action_visible:actions.some(s=>/go live|iniciar live|transmitir ao vivo/.test(s)),
        download_only_visible:actions.some(s=>/baixe o live studio|download live studio/.test(s))
      };
    }""")
    parsed = urlsplit(page.url)
    host = (parsed.hostname or "").lower()
    same_service = host.endswith(".tiktok.com") or host == "tiktok.com"
    outcome = (
        "LOGIN_REQUIRED" if signal["login_prompt"] or "/login" in (parsed.path or "").lower()
        else "TIKTOK_PAGE_REACHED" if status == 200 and same_service
        else "PAGE_NOT_CONFIRMED"
    )
    return {
        "stage": stage, "status": status, "outcome": outcome,
        "tiktok_host": same_service, "login_prompt": signal["login_prompt"],
        "owner_media_links": signal["owner_media_links"],
        "owner_marker": signal["owner_marker"],
        "producer_marker": signal["producer_marker"],
        "rtmp_label_visible": signal["rtmp_label_visible"],
        "live_action_visible": signal["live_action_visible"],
        "download_only_visible": signal["download_only_visible"]
    }

def main():
    from playwright.sync_api import sync_playwright
    state = state_from_secret()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
        try:
            context = browser.new_context(storage_state=state, locale="pt-BR", viewport={"width":1366,"height":850})
            try:
                page = context.new_page()
                studio = inspect(page, "studio")
                print("TIKTOK_LIVE_STUDIO_PROBE=" + json.dumps(studio, sort_keys=True), flush=True)
                if studio["outcome"] != "TIKTOK_PAGE_REACHED":
                    print("TIKTOK_LIVE_ACCESS_STATUS=SESSION_OR_STUDIO_UNVERIFIED", flush=True)
                    return 0
                producer = inspect(page, "producer")
                print("TIKTOK_LIVE_PRODUCER_PROBE=" + json.dumps(producer, sort_keys=True), flush=True)
                if producer["outcome"] != "TIKTOK_PAGE_REACHED":
                    print("TIKTOK_LIVE_ACCESS_STATUS=PRODUCER_UNVERIFIED", flush=True)
                elif producer["rtmp_label_visible"]:
                    print("TIKTOK_LIVE_ACCESS_STATUS=RTMP_UI_POSSIBLE_REQUIRES_MANUAL_ELIGIBILITY_CONFIRMATION", flush=True)
                else:
                    print("TIKTOK_LIVE_ACCESS_STATUS=NO_RTMP_CONTROL_VISIBLE_ELIGIBILITY_UNKNOWN", flush=True)
                return 0
            finally:
                context.close()
        finally:
            browser.close()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        reason = str(exc)
        if not re.fullmatch(r"[A-Z0-9_]+", reason):
            reason = "PROBE_SETUP_FAILED"
        print("TIKTOK_LIVE_ACCESS_STATUS=" + reason, flush=True)
        sys.exit(0)
