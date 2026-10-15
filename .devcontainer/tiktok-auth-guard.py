#!/usr/bin/env python3
"""Private TikTok Codespaces identity guard and secure session handoff.

No credentials, cookies, tokens, screenshots, or page text are returned by this
service. A verified storage state is piped directly into GitHub Actions secrets.
"""
import asyncio
import html
import json
import os
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PORT = 8766
EXPECTED = os.getenv("EXPECTED_TIKTOK_USERNAME", "universo.anthares").lstrip("@").lower()
CSRF = secrets.token_urlsafe(32)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "direct-tiktok-publisher"))


async def verify_and_state(include_state=False):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223", timeout=8000)
        try:
            if not browser.contexts:
                return {"chrome_connected": True, "identity_verified": False, "reason": "context_missing"}, None
            context = browser.contexts[0]
            page = await context.new_page()
            try:
                await page.goto("https://www.tiktok.com/foryou", wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3500)
                # Reuse the same strict account gate used by publication workflows.
                import tiktok_worker as tw
                # tiktok_worker is sync-oriented; reproduce its strong signals without
                # exporting any content from the private browser.
                exact = False
                try:
                    raw = await page.locator("#__UNIVERSAL_DATA_FOR_REHYDRATION__").text_content(timeout=5000)
                    data = json.loads(raw or "{}")
                    user = (data.get("__DEFAULT_SCOPE__", {}).get("webapp.app-context", {}).get("user", {}) or {})
                    exact = str(user.get("uniqueId") or "").strip().lower() == EXPECTED
                except Exception:
                    exact = False
                if not exact:
                    await page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(2500)
                    exact = ("/@" + EXPECTED) in page.url.lower()
                if not exact:
                    return {"chrome_connected": True, "identity_verified": False, "reason": "expected_account_not_proven"}, None
                await page.goto("https://www.tiktok.com/tiktokstudio/upload?from=webapp", wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(2500)
                login_gate = await page.locator('input[type="password"]').count() > 0
                if login_gate or "login" in page.url.lower():
                    return {"chrome_connected": True, "identity_verified": False, "studio_verified": False, "reason": "studio_login_gate"}, None
                state = await context.storage_state()
                count = len(state.get("cookies") or [])
                result = {"chrome_connected": True, "identity_verified": True, "studio_verified": True, "cookie_count": count}
                return result, state if include_state else None
            finally:
                await page.close()
        finally:
            await browser.close()


def secure_handoff():
    result, state = asyncio.run(verify_and_state(include_state=True))
    if not result.get("identity_verified") or not result.get("studio_verified") or not state:
        return {**result, "persisted": False}
    payload = json.dumps(state, separators=(",", ":"))
    proc = subprocess.run(
        ["gh", "secret", "set", "TIKTOK_STORAGE_STATE", "--repo", "UniversoAnthares/anthares-kwai-runner", "--body", payload],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=35,
    )
    if proc.returncode != 0:
        return {**result, "persisted": False, "reason": "github_secret_write_failed"}
    trigger = subprocess.run(
        ["gh", "workflow", "run", "tiktok-session-secret-to-vault.yml", "--repo", "UniversoAnthares/anthares-kwai-runner"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=25,
    )
    return {**result, "persisted": trigger.returncode == 0, "workflow_triggered": trigger.returncode == 0}


def render(message="", data=None):
    proof = ""
    if data is not None:
        safe = {k: v for k, v in data.items() if k not in {"state", "cookies", "token"}}
        proof = "<pre>" + html.escape(json.dumps(safe, indent=2, ensure_ascii=False)) + "</pre>"
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Anthares TikTok</title></head><body style='font-family:system-ui;max-width:760px;margin:40px auto;padding:0 20px'><h1>Anthares Browser · TikTok</h1><p>Conta obrigatória: <b>@{EXPECTED}</b></p><p>{html.escape(message)}</p>{proof}<form method='post'><input type='hidden' name='csrf' value='{CSRF}'><button name='action' value='verify'>Verificar identidade</button> <button name='action' value='persist'>Salvar sessão com segurança</button></form><p>Nunca cole senha, código de verificação ou cookies no chat.</p></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, status=200):
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self._send(render("Faça o login no Chrome remoto privado e depois verifique."))

    def do_POST(self):
        length = min(int(self.headers.get("Content-Length", "0") or 0), 4096)
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        if form.get("csrf", [""])[0] != CSRF:
            return self._send(render("CSRF inválido."), 403)
        action = form.get("action", [""])[0]
        try:
            if action == "verify":
                result, _ = asyncio.run(verify_and_state(False))
                return self._send(render("Identidade confirmada." if result.get("identity_verified") else "Identidade ainda não confirmada.", result))
            if action == "persist":
                result = secure_handoff()
                return self._send(render("Sessão enviada ao cofre seguro." if result.get("persisted") else "Sessão não foi persistida.", result), 200 if result.get("persisted") else 503)
            return self._send(render("Ação inválida."), 400)
        except Exception as exc:
            return self._send(render("Falha de verificação.", {"ok": False, "reason": type(exc).__name__}), 503)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
