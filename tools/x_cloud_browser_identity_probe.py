#!/usr/bin/env python3
"""Read-only identity check: Anthares X encrypted vault -> isolated GitHub Chromium.

This tool never posts, uploads media, changes a cookie vault, or manipulates
the Windows desktop. No tokens/cookies/page HTML are printed.
"""
from __future__ import annotations
import os
import re
import json
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, "infra")
import anthares_runtime_browser_local as vault


def run():
    if not os.getenv("ARA_SHARED"):
        raise RuntimeError("X_SHARED_SECRET_NOT_CONFIGURED")
    state = vault._vault_pull()
    if not state or not isinstance(state.get("cookies"), list):
        raise RuntimeError("X_ENCRYPTED_VAULT_EMPTY")
    auth = {c.get("name") for c in state["cookies"]
            if str(c.get("domain") or "").lstrip(".").endswith(("x.com", "twitter.com"))}
    if not {"auth_token", "ct0", "twid"}.issubset(auth):
        raise RuntimeError("X_VAULT_MISSING_AUTHENTICATED_COOKIES")
    print("X_CLOUD_VAULT_DECRYPTED=True", flush=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            # A virtual Linux display remains completely invisible to the user.
            # Test headed Chromium like the proven offscreen Windows browser.
            headless=os.getenv("ANTHARES_X_VIRTUAL_DISPLAY") != "1",
            timeout=35000, args=[
                "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-background-networking", "--mute-audio",
            ]
        )
        try:
            context = browser.new_context(storage_state=state, locale="pt-BR",
                                          viewport={"width":1365,"height":768})
            page = context.new_page()
            page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=50000)
            deadline = time.monotonic() + 45
            handle = ""
            while time.monotonic() < deadline:
                if any(text in page.url for text in ("/login", "/i/jf/onboarding", "/i/flow/login")):
                    raise RuntimeError("X_CLOUD_LOGIN_REQUIRED")
                link = page.locator('a[data-testid="AppTabBar_Profile_Link"]')
                if link.count():
                    h = (link.first.get_attribute("href") or "").lstrip("/").split("/")[0].lower()
                    if h == "lucasyahn":
                        handle = h
                        break
                switcher = page.locator('[data-testid="SideNav_AccountSwitcher_Button"]')
                if switcher.count():
                    body = switcher.first.inner_text(timeout=5000)
                    ids = re.findall(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{1,15})(?![A-Za-z0-9_])", body)
                    if ids == ["lucasyahn"]:
                        handle = ids[0]
                        break
                    if ids:
                        raise RuntimeError("X_CLOUD_ACCOUNT_MISMATCH")
                page.wait_for_timeout(1600)
            if handle != "lucasyahn":
                # Sanitized machine-readable browser diagnostics: booleans and
                # coarse page category only, never HTML/cookies/challenge text.
                state = page.evaluate("""() => ({
                    route: location.pathname === '/home' ? 'home'
                           : (location.pathname.includes('login') ? 'login' : 'other'),
                    switcherPresent: !!document.querySelector('[data-testid="SideNav_AccountSwitcher_Button"]'),
                    profilePresent: !!document.querySelector('a[data-testid="AppTabBar_Profile_Link"]'),
                    composerPresent: !!document.querySelector('[data-testid="SideNav_NewTweet_Button"]'),
                    loginPrompt: !!document.querySelector('input[autocomplete="username"]')
                })""")
                print("X_CLOUD_BROWSER_DOM_DIAG=" + json.dumps(state, sort_keys=True), flush=True)
                raise RuntimeError("X_CLOUD_ACCOUNT_NOT_PROVEN")
            print("X_CLOUD_BROWSER_IDENTITY_OK=lucasyahn", flush=True)
            print("X_CLOUD_BROWSER_PUBLICATION_PREFLIGHT_READY=True", flush=True)
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("X_CLOUD_PREFLIGHT_ERROR_TYPE=" + type(exc).__name__, flush=True)
        # Emit only fixed diagnostic identifiers; never print browser cookies,
        # challenge pages, tokens, URLs with parameters or exception messages.
        SAFE_CODES = {
            "X_SHARED_SECRET_NOT_CONFIGURED",
            "X_ENCRYPTED_VAULT_EMPTY",
            "X_VAULT_MISSING_AUTHENTICATED_COOKIES",
            "X_CLOUD_LOGIN_REQUIRED",
            "X_CLOUD_ACCOUNT_MISMATCH",
            "X_CLOUD_ACCOUNT_NOT_PROVEN",
        }
        code = str(exc)
        if isinstance(exc, RuntimeError) and code in SAFE_CODES:
            print("X_CLOUD_PREFLIGHT_ERROR_CODE=" + code, flush=True)
        raise SystemExit(2)
