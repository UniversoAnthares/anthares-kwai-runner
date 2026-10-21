#!/usr/bin/env python3
"""One-time local-only handoff of an explicitly authorized isolated TikTok profile.

Run from a trusted Windows self-hosted Actions job. Never prints or writes
the browser session. The encrypted state is uploaded directly to its own vault.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))

EXPECTED="lucasrosalem4"
VAULT="https://anthares-x-vault.anthares1.workers.dev/browser-state/tiktok/lucasrosalem4"


def verified_identity(url, hydration):
    """Only accept the authenticated user's own /profile redirect/hydration."""
    host=urlparse(url).hostname
    if host not in ("www.tiktok.com","tiktok.com"):
        return False
    match=re.search(r"/@([^/?#]+)",url,re.I)
    redirected=(match.group(1).casefold() if match else "")
    user=""
    try:
        obj=json.loads(hydration or "{}")
        user=str(obj.get("__DEFAULT_SCOPE__",{}).get("webapp.app-context",{})
                 .get("user",{}).get("uniqueId") or "").casefold()
    except (TypeError,ValueError,AttributeError):
        return False
    if user and user!=EXPECTED:
        return False
    return redirected==EXPECTED or user==EXPECTED


def main():
    if os.name!="nt":
        raise RuntimeError("WINDOWS_HOST_REQUIRED")
    if os.getenv("GITHUB_REF")!="refs/heads/main":
        raise RuntimeError("TRUSTED_MAIN_WORKFLOW_REQUIRED")
    if not os.getenv("ARA_SHARED"):
        raise RuntimeError("VAULT_SIGNING_SECRET_NOT_BOUND")
    os.environ["EXPECTED_TIKTOK_USERNAME"]=EXPECTED
    os.environ["ANTHARES_TIKTOK_SESSION_VAULT_URL"]=VAULT
    from tiktok_session_authority import persist_canonical_state
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.connect_over_cdp("http://127.0.0.1:9228",timeout=15000)
        try:
            contexts=browser.contexts
            if len(contexts)!=1:
                raise RuntimeError("ISOLATED_PROFILE_CONTEXT_NOT_UNIQUE")
            context=contexts[0]
            page=context.new_page()
            try:
                page.goto("https://www.tiktok.com/profile",wait_until="domcontentloaded",timeout=45000)
                page.wait_for_timeout(2000)
                if "/login" in page.url.lower() or page.locator('input[type="password"]').count():
                    raise RuntimeError("SECONDARY_TIKTOK_LOGIN_REQUIRED")
                try:
                    hydration=page.locator("#__UNIVERSAL_DATA_FOR_REHYDRATION__").text_content(timeout=5000)
                except Exception:
                    hydration=""
                if not verified_identity(page.url,hydration):
                    raise RuntimeError("SECONDARY_TIKTOK_ACCOUNT_NOT_VERIFIED")
                state=context.storage_state()
                if not isinstance(state.get("cookies"),list) or not state["cookies"]:
                    raise RuntimeError("SECONDARY_TIKTOK_SESSION_EMPTY")
                if not any(x.get("name") in ("sessionid","sessionid_ss","sid_tt")
                           and "tiktok.com" in str(x.get("domain",""))
                           for x in state["cookies"]):
                    raise RuntimeError("SECONDARY_TIKTOK_AUTH_COOKIE_MISSING")
                receipt=persist_canonical_state(state)
                if receipt.get("authority")!="runtime" or receipt.get("vault_url")!=VAULT:
                    raise RuntimeError("SECONDARY_TIKTOK_VAULT_RECEIPT_INVALID")
                print("CORTES_TIKTOK_LUCAROSALEM_IDENTITY_VERIFIED=1",flush=True)
                print("CORTES_TIKTOK_LUCAROSALEM_ENCRYPTED_SESSION_SAVED=1",flush=True)
            finally:
                page.close()
        finally:
            browser.close()
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("CORTES_TIKTOK_LUCAROSALEM_CAPTURE_BLOCKED="+type(exc).__name__+
              ":"+str(exc)[:85],file=sys.stderr,flush=True)
        sys.exit(2)
