import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from playwright.async_api import async_playwright

OUT = Path("kwai-session-results")
OUT.mkdir(exist_ok=True)
CACHE = Path(".kwai-session-cache")
CACHE.mkdir(exist_ok=True)
ENC = CACHE / "kwai-session.enc"
STATE = CACHE / "storage-state.json"
SECRET = os.environ.get("KWAI_SESSION_KEY", "")


def fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET.encode()).digest())
    return Fernet(key)


def restore_state(result):
    result["session_key_present"] = bool(SECRET)
    result["encrypted_session_found"] = ENC.exists()
    result["session_restored"] = False
    if not (SECRET and ENC.exists()):
        return
    try:
        STATE.write_bytes(fernet().decrypt(ENC.read_bytes()))
        result["session_restored"] = True
    except (InvalidToken, ValueError) as exc:
        result["session_restore_error"] = type(exc).__name__


def persist_state(result):
    if not SECRET or not STATE.exists():
        return
    ENC.write_bytes(fernet().encrypt(STATE.read_bytes()))
    STATE.unlink(missing_ok=True)
    result["encrypted_session_written"] = True


async def open_login(page):
    targets = ["https://www.kwai.com/", "https://www.kwai.com/@universo.anthares"]
    for target in targets:
        await page.goto(target, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1400)
        login = page.get_by_text("Fazer login", exact=True)
        if await login.count():
            await login.first.click(timeout=3000, force=True)
            await page.wait_for_timeout(900)
            return {"opened": True, "source": target}
    return {"opened": False, "source": None}


async def probe_method(browser, method):
    ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, locale="pt-BR", timezone_id="America/Sao_Paulo")
    page = await ctx.new_page()
    item = {"method": method, "opened_login": False, "found": 0}
    try:
        opened = await open_login(page)
        item["opened_login"] = opened["opened"]
        item["login_source"] = opened["source"]
        locator = page.get_by_text(method, exact=True)
        item["found"] = await locator.count()
        before_pages = len(ctx.pages)
        if item["found"]:
            try:
                await locator.first.click(timeout=3000, force=True)
            except Exception:
                await locator.first.evaluate("el => el.click()")
            await page.wait_for_timeout(1200)
        item["pages_after"] = len(ctx.pages)
        item["popup_opened"] = len(ctx.pages) > before_pages
        item["url"] = page.url
        item["dialogs"] = await page.locator('[role="dialog"]').count()
        item["inputs"] = await page.locator("input").evaluate_all("els => els.map(e => ({type:e.type, placeholder:e.placeholder})).slice(0,8)")
        texts = await page.locator('[role="dialog"]').all_inner_texts()
        item["dialog_text"] = texts[:2]
        if item["popup_opened"]:
            popup = ctx.pages[-1]
            try:
                await popup.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            item["popup_url"] = popup.url
            item["popup_title"] = await popup.title()
    except Exception as exc:
        item["error"] = str(exc)[:220]
    await ctx.close()
    return item


async def main():
    result = {"mode": "remote_chrome_session", "authenticated": False}
    restore_state(result)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])

        result["auth_methods"] = []
        for method in ["Use o telefone", "Continue com o Google"]:
            result["auth_methods"].append(await probe_method(browser, method))

        kwargs = {"viewport": {"width": 1440, "height": 900}, "locale": "pt-BR", "timezone_id": "America/Sao_Paulo"}
        if result.get("session_restored") and STATE.exists():
            kwargs["storage_state"] = str(STATE)
        ctx = await browser.new_context(**kwargs)
        page = await ctx.new_page()
        try:
            await page.goto("https://www.kwai.com/@universo.anthares", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1500)
            login_controls = await page.get_by_text("Fazer login", exact=True).count()
            result["login_controls_after_restore"] = login_controls
            # Login-button absence is not proof of account identity.
            result["identity_verified"] = False
            result["identity_verification_method"] = "not_configured"
            result["authenticated"] = False
            if result["authenticated"]:
                await ctx.storage_state(path=str(STATE), indexed_db=True)
                persist_state(result)
        except Exception as exc:
            result["verification_error"] = str(exc)[:220]
        await ctx.close()
        await browser.close()

    if not result["authenticated"]:
        result["action_required"] = "authenticate_once_in_remote_chrome"
    if not SECRET:
        result["persistence_blocker"] = "KWAI_SESSION_KEY_missing"

    (OUT / "session-probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print("KWAI_SESSION_PROBE=" + json.dumps(result, ensure_ascii=False))


asyncio.run(main())
