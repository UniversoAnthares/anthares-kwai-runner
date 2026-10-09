#!/usr/bin/env python3
"""Codespaces-only, allowlisted GitHub issue -> Chrome CDP control bridge.

The GitHub issue is public: NEVER send secrets, page text, cookies or screenshots.
Only owner-authored, explicitly allowlisted commands are processed.
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

REPO = "UniversoAnthares/anthares-kwai-runner"
ISSUE = 12
OWNER = "universoanthares"
STATE = Path.home() / ".kwai-remote-private" / "bridge-seen.json"
COMMAND = re.compile(r"^KWAI_BRIDGE_CMD (inspect|open_home|profile_check) ([a-zA-Z0-9_-]{12,64})$")
def gh(method, endpoint, data=None):
    args = ["gh", "api", "--method", method, endpoint]
    if data is not None:
        args += ["--input", "-"]
    p = subprocess.run(args, input=json.dumps(data) if data is not None else None,
                       text=True, capture_output=True, timeout=20, check=True)
    return json.loads(p.stdout) if p.stdout.strip() else {}

async def browser_action(action):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=7000)
        try:
            if not browser.contexts:
                return {"chrome_connected": True, "context_present": False}
            context = browser.contexts[0]
            if action == "open_home":
                page = await context.new_page()
                await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=15000)
                await page.close()
            if action == "profile_check":
                kwai_pages = [t for t in context.pages
                              if urlsplit(t.url).hostname in ("www.kwai.com", "kwai.com")]
                if not kwai_pages:
                    return {"chrome_connected": True, "kwai_tab_present": False,
                            "profile_check": "no_kwai_tab"}
                page = kwai_pages[0]
                try:
                    await page.bring_to_front()
                    # Read only boolean indicators, never profile text or session material.
                    evidence = await page.evaluate("""() => ({
                      logout_visible: [...document.querySelectorAll('a,button,[role=menuitem]')]
                        .some(e => /^(log out|logout|sair)$/i.test((e.innerText||'').trim())),
                      login_visible: [...document.querySelectorAll('a,button,[role=button]')]
                        .some(e => /^(log in|login|sign in|entrar)$/i.test((e.innerText||'').trim())),
                      profile_link_present: [...document.querySelectorAll('a[href]')]
                        .some(e => /kwai.com\\/(?:@|profile|user)/i.test(e.href||''))
                    })""")
                except Exception:
                    return {"chrome_connected": True, "kwai_tab_present": True,
                            "profile_check": "ui_inspection_failed"}
                return {"chrome_connected": True, "kwai_tab_present": True,
                        "profile_check": "complete",
                        "logout_visible": bool(evidence.get("logout_visible")),
                        "login_visible": bool(evidence.get("login_visible")),
                        "profile_link_present": bool(evidence.get("profile_link_present")),
                        "identity_verified": False}
            hosts = sorted({urlsplit(t.url).hostname for t in context.pages
                            if urlsplit(t.url).hostname in ("www.kwai.com", "kwai.com")})
            return {"chrome_connected": True, "kwai_tab_present": bool(hosts),
                    "kwai_home_opened": action == "open_home"}
        finally:
            await browser.close()

def main():
    import asyncio
    STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    seen = set(json.loads(STATE.read_text())) if STATE.exists() else set()
    print("KWAI_BRIDGE_READY=issue-12;commands=inspect,open_home,profile_check;no_session_export", flush=True)
    while True:
        try:
            comments = gh("GET", f"repos/{REPO}/issues/{ISSUE}/comments?per_page=100")
            for c in comments:
                cid = str(c["id"])
                if cid in seen:
                    continue
                seen.add(cid)
                STATE.write_text(json.dumps(sorted(seen)[-500:]))
                STATE.chmod(0o600)
                if (c.get("user") or {}).get("login", "").lower() != OWNER:
                    continue
                match = COMMAND.fullmatch((c.get("body") or "").strip())
                if not match:
                    continue
                action, nonce = match.groups()
                try:
                    result = asyncio.run(browser_action(action))
                    outcome = {"nonce": nonce, "status": "ok", **result}
                except Exception:
                    outcome = {"nonce": nonce, "status": "error", "reason": "chrome_unavailable_or_navigation_failed"}
                gh("POST", f"repos/{REPO}/issues/{ISSUE}/comments", {"body": "KWAI_BRIDGE_RESULT " + json.dumps(outcome, sort_keys=True)})
        except Exception:
            print("KWAI_BRIDGE_POLL_RETRY", flush=True)
        time.sleep(8)

if __name__ == "__main__":
    main()
