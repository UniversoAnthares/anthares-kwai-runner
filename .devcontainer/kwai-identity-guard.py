#!/usr/bin/env python3
"""Private Codespaces Chrome identity inspector. Never records credentials or cookies."""
import asyncio
import hmac
import html
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

EXPECTED = os.getenv("KWAI_EXPECTED_HANDLE", "universo.anthares").lstrip("@").lower()
CSRF = secrets.token_urlsafe(32)
PORT = 8765
PROFILE_URL = "https://www.kwai.com/@" + EXPECTED


def assess_authentication(evidence):
    """Visible account-menu logout proves signed-in UI, not account ownership."""
    return evidence.get("account_menu_logout_visible") is True


def assess_evidence(evidence):
    """Verify exact account identity; a display name or public URL is insufficient."""
    if evidence.get("profile_url_matches") is not True:
        return False
    if evidence.get("login_controls_absent") is not True:
        return False
    # A visible signed-in menu is required on BOTH verification paths.
    if not assess_authentication(evidence):
        return False
    legacy = (evidence.get("owner_edit_control_visible") is True
              and evidence.get("account_menu_handle_matches") is True)
    # Modern Kwai menu shows a display name; require an exact account
    # profile link next to the authenticated Log out control instead.
    menu = evidence.get("account_menu_profile_link_matches") is True
    return legacy or menu


async def inspect_open_account_menu(context):
    """Read the existing authenticated Chrome tabs without clicking Log out.

    A visible logout control proves only signed-in UI. Account identity is
    verified only if a link to the expected @handle is in the same menu.
    No cookies, tokens, DOM text or display names are returned or logged.
    """
    result = {"account_menu_logout_visible": False,
              "account_menu_profile_link_matches": False}
    script = r"""(expected) => {
      const visible = (el) => {
        const style = getComputedStyle(el), box = el.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden'
          && box.width > 0 && box.height > 0;
      };
      const logout = /^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o)$/i;
      const leaves = [...document.querySelectorAll('a,button,[role="menuitem"],span,div')];
      let signedIn = false, exactProfile = false;
      for (const el of leaves) {
        if (!visible(el) || !logout.test((el.innerText || '').trim())) continue;
        // Do not mistake a whole page containing 'Log out' for a menu item.
        if ((el.innerText || '').length > 32) continue;
        signedIn = true;
        let ancestor = el;
        for (let depth = 0; depth < 6 && ancestor; depth++, ancestor = ancestor.parentElement) {
          const links = [...ancestor.querySelectorAll('a[href]')];
          if (links.some(a => {
            try {
              const url = new URL(a.getAttribute('href'), location.href);
              return url.hostname === 'www.kwai.com'
                && url.pathname.replace(/\/$/, '').toLowerCase() === '/@' + expected;
            } catch { return false; }
          })) { exactProfile = true; break; }
        }
      }
      return {account_menu_logout_visible: signedIn,
              account_menu_profile_link_matches: exactProfile};
    }"""
    for tab in list(context.pages):
        try:
            url = urlsplit(tab.url)
            if url.scheme != "https" or url.hostname != "www.kwai.com":
                continue
            observed = await asyncio.wait_for(tab.evaluate(script, EXPECTED), timeout=3)
            for key in result:
                result[key] = result[key] or observed.get(key) is True
        except Exception:
            # A closed tab must not turn missing evidence into a positive result.
            continue
    return result


async def inspect_browser():
    from playwright.async_api import async_playwright

    result = {
        "chrome_connected": False,
        "expected_account": "@" + EXPECTED,
        "identity_verified": False,
        "verification_basis": "owner_profile_control_and_authenticated_account_menu",
    }
    async with async_playwright() as p:
        browser = await asyncio.wait_for(
            p.chromium.connect_over_cdp("http://127.0.0.1:9222"),
            timeout=8,
        )
        result["chrome_connected"] = True
        if not browser.contexts:
            result["reason"] = "no_chrome_context"
            return result
        context = browser.contexts[0]
        account_menu = await inspect_open_account_menu(context)
        page = await context.new_page()
        try:
            await page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(1600)
            current = urlsplit(page.url)
            profile_matches = (
                current.scheme == "https"
                and current.hostname == "www.kwai.com"
                and current.path.rstrip("/").lower() == "/@" + EXPECTED
            )
            owner_controls = await page.get_by_text(
                "Editar perfil", exact=True
            ).count() + await page.get_by_text(
                "Edit profile", exact=True
            ).count()
            login_controls = (
                await page.get_by_text("Fazer login", exact=True).count()
                + await page.get_by_text("Log in", exact=True).count()
                + await page.get_by_text("Entrar", exact=True).count()
            )
            # Account-menu proof must be independent of public profile content.
            # A public profile showing @handle is NOT authentication evidence.
            menu_evidence = await page.evaluate(
                """(handle) => {
                  const selectors = [
                    '[role="menu"]', '[data-testid*="account"]',
                    '[data-testid*="user-menu"]', '[aria-label*="account"]',
                    '[aria-label*="Conta"]'
                  ];
                  const els = [...document.querySelectorAll(selectors.join(','))];
                  return els.some(e => {
                    const value = (e.textContent || '') + ' ' +
                      (e.getAttribute('aria-label') || '');
                    return value.toLowerCase().includes('@' + handle);
                  });
                }""",
                EXPECTED,
            )
            evidence = {
                "profile_url_matches": profile_matches,
                "owner_edit_control_visible": owner_controls > 0,
                "account_menu_handle_matches": bool(menu_evidence),
                "login_controls_absent": login_controls == 0,
                "account_menu_logout_visible": account_menu["account_menu_logout_visible"],
                "account_menu_profile_link_matches": account_menu["account_menu_profile_link_matches"],
            }
            result["authenticated_ui_detected"] = assess_authentication(evidence)
            result["evidence"] = evidence
            result["identity_verified"] = assess_evidence(evidence)
            result["reason"] = (
                "strict_ui_identity_proven"
                if result["identity_verified"]
                else ("authenticated_account_handle_unconfirmed"
                      if result["authenticated_ui_detected"]
                      else "insufficient_authenticated_owner_evidence")
            )
            result["persistence_permitted"] = False
            result["server_identity_verified"] = False
            # A UI observation is not an independent server-side identity proof.
        finally:
            await page.close()
            # Closing a CDP client disconnects the inspector from Chrome.
            await browser.close()
    return result


def page_html(message=""):
    safe = html.escape(message)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kwai Chrome remoto — identidade</title>
<style>body{{font:16px system-ui;max-width:750px;margin:3rem auto;padding:1rem;
line-height:1.5;background:#12141a;color:#f3f3f3}}
a{{color:#a4c7ff}}button{{padding:.8rem 1.2rem;font-size:1rem}}
code,pre{{white-space:pre-wrap;word-break:break-word}}
</style></head><body>
<h1>Kwai — navegador remoto privado</h1>
<p>Conta esperada: <strong>@{html.escape(EXPECTED)}</strong>.</p>
<p>Abra a porta <strong>6080</strong> em <strong>PORTS</strong> no Codespaces
e mantenha a visibilidade <strong>Private</strong>.
Use a tela do Chrome remoto para entrar no Kwai. Não envie senhas,
códigos de verificação ou cookies pelo chat ou por arquivos públicos.</p>
<p>Esta verificação lê somente indicadores de interface.
Não extrai, grava ou publica cookies, senhas ou tokens.</p>
<form method="post" action="/check">
<input type="hidden" name="csrf" value="{CSRF}">
<button type="submit">Verificar identidade da conta</button>
</form><pre>{safe}</pre>
<p>A sessão não será exportada enquanto a identidade não estiver comprovada.</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # No request bodies, query strings, cookies or tokens in logs.
        print("KWAI_IDENTITY_HTTP_REQUEST", flush=True)

    def send(self, code, payload, kind="text/html; charset=utf-8"):
        raw = payload.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self.send(200, json.dumps({"ready": True, "identity_verified": False}),
                      "application/json; charset=utf-8")
        elif self.path == "/":
            self.send(200, page_html())
        else:
            self.send(404, "Not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path != "/check":
            self.send(404, "Not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 2048:
            self.send(400, "Invalid request", "text/plain; charset=utf-8")
            return
        fields = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        provided = fields.get("csrf", [""])[0]
        if not hmac.compare_digest(provided, CSRF):
            self.send(403, "Forbidden", "text/plain; charset=utf-8")
            return
        try:
            result = asyncio.run(asyncio.wait_for(inspect_browser(), timeout=32))
        except Exception as exc:
            result = {"identity_verified": False,
                      "error": type(exc).__name__,
                      "reason": "inspector_unavailable"}
        if self.headers.get("Accept", "").split(",")[0].strip() == "application/json":
            self.send(200, json.dumps(result, ensure_ascii=False),
                      "application/json; charset=utf-8")
        else:
            self.send(200, page_html(json.dumps(result, indent=2, ensure_ascii=False)))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("KWAI_IDENTITY_GUARD_READY=private_port_8765", flush=True)
    server.serve_forever()
