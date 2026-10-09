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
    menu = (evidence.get("account_menu_profile_link_matches") is True
            or evidence.get("account_menu_profile_navigation_matches") is True)
    return legacy or menu


async def open_account_menu_in_probe_page(page):
    """Click only the top-right avatar in the disposable inspection tab.

    This is a UI-only operation. Never click Log out, submit credentials, or
    navigate a user's existing tab. Failure to locate the avatar fails closed.
    """
    script = r"""() => {
      const visible = el => {
        const r = el.getBoundingClientRect();
        const st = getComputedStyle(el);
        return r.width >= 16 && r.height >= 16 && r.width <= 100
          && r.height <= 100 && st.visibility !== 'hidden'
          && st.display !== 'none';
      };
      // The Kwai desktop header places the signed-in avatar at far right.
      // Restrict candidates to the header, excluding feed avatars and menus.
      const avatars = [...document.querySelectorAll(
        'header img, [role="banner"] img, img, [aria-label*="avatar" i], [data-testid*="avatar" i]'
      )].filter(el => {
        const r = el.getBoundingClientRect();
        return visible(el) && r.left >= innerWidth * .75
          && r.top >= 0 && r.top <= 180;
      }).sort((a,b) => b.getBoundingClientRect().right
                        - a.getBoundingClientRect().right);
      const avatar = avatars[0];
      if (!avatar) return false;
      // Dispatch the click to the avatar itself; React receives the bubbled
      // event on the menu trigger. Never click any item in the dropdown.
      avatar.click();
      return true;
    }"""
    try:
        # Real pointer events are required by Kwai's account trigger.
        # The older DOM .click() reported success but did not open the menu
        # in the user's live Codespaces Chrome (issue #12 proof).
        points = await page.evaluate(r"""() => {
          const visible = el => {
            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
            return r.width>=16&&r.height>=16&&r.width<=100&&r.height<=100&&
              s.display!=='none'&&s.visibility!=='hidden';
          };
          return [...document.querySelectorAll('img')].filter(el=>{
            const r=el.getBoundingClientRect();
            if(!visible(el)||r.left<innerWidth*.60||r.top>200||
               el.closest('a[href]'))return false;
            const label=(el.parentElement?.innerText||'').trim();
            return label.length<70 &&
              !/(upload|publicar|postar|log\s*in|sign\s*in|logout|log\s*out|sair)/i.test(label);
          }).sort((a,b)=>b.getBoundingClientRect().right-
                            a.getBoundingClientRect().right).slice(0,3)
            .map(el=>{const r=el.getBoundingClientRect();
              return {x:r.left+r.width/2,y:r.top+r.height/2}});
        }""")
        for point in points:
            await page.mouse.move(point["x"], point["y"])
            await page.mouse.click(point["x"], point["y"])
            await page.wait_for_timeout(450)
            opened = await page.evaluate(r"""() => {
              const visible=el=>{
                const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                return r.width>0&&r.height>0&&s.display!=='none'&&
                  s.visibility!=='hidden';
              };
              return [...document.querySelectorAll(
                'a,button,span,div,[role="menuitem"]'
              )].some(el=>{
                const t=(el.innerText||'').trim();
                return visible(el)&&t.length<=32&&
                  /^(log\s*out|logout|sign\s*out|sair)$/i.test(t);
              });
            }""")
            if opened:
                return True
            await page.mouse.click(12, 220)
        # Keep the legacy DOM click as a last resort for older Kwai UIs.
        return await asyncio.wait_for(page.evaluate(script), timeout=3) is True
    except Exception:
        return False


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


async def inspect_own_profile_navigation(context):
    """Follow the signed-in account row from a NEW tab, never a user's tab.

    This can prove the exact handle when Kwai's menu shows only a display name
    without an href. No logout, credentials, cookies or session exports.
    """
    outcome = {"account_menu_profile_navigation_attempted": False,
               "account_menu_profile_navigation_matches": False}
    page = await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded",
                        timeout=12000)
        await page.wait_for_timeout(700)
        if not await open_account_menu_in_probe_page(page):
            return outcome
        await page.wait_for_timeout(350)
        script = r"""() => {
          const visible = el => {
            const r = el.getBoundingClientRect(), st = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && st.display !== 'none'
              && st.visibility !== 'hidden';
          };
          const logout = /^(log\s*out|logout|sign\s*out|sair)$/i;
          const nodes = [...document.querySelectorAll('button,a,[role="menuitem"]'),
                         ...document.querySelectorAll('span,div')];
          const logoutEl = nodes.find(el => visible(el) &&
            (el.innerText || '').length <= 32 &&
            logout.test((el.innerText || '').trim()));
          if (!logoutEl) return false;
          const lr = logoutEl.getBoundingClientRect();
          let ancestor = logoutEl.parentElement;
          for (let depth = 0; depth < 6 && ancestor; depth++, ancestor = ancestor.parentElement) {
            const ar = ancestor.getBoundingClientRect();
            // Only the small dropdown panel near the top-right may be used.
            if (ar.width > 360 || ar.height > 360 ||
                ar.right < innerWidth * .7) continue;
            const images = [...ancestor.querySelectorAll('img')].filter(img => {
              const r = img.getBoundingClientRect();
              return visible(img) && r.width >= 16 && r.height >= 16
                && r.top < lr.top && r.bottom >= lr.top - 150
                && r.left >= innerWidth * .65;
            }).sort((a,b) => b.getBoundingClientRect().bottom -
                             a.getBoundingClientRect().bottom);
            if (images.length) {
              // The avatar above 'Log out' is the account row. No other item
              // in the dropdown is clicked, especially not Log out.
              const r = images[0].getBoundingClientRect();
              return {x:r.left+r.width/2,y:r.top+r.height/2};
            }
          }
          return false;
        }"""
        point = await asyncio.wait_for(page.evaluate(script), timeout=3)
        if isinstance(point, dict):
            await page.mouse.click(point["x"], point["y"])
            outcome["account_menu_profile_navigation_attempted"] = True
        if not outcome["account_menu_profile_navigation_attempted"]:
            return outcome
        for _ in range(8):
            await page.wait_for_timeout(300)
            current = urlsplit(page.url)
            if current.scheme == "https" and current.hostname == "www.kwai.com":
                path = current.path.rstrip("/").lower()
                if path.startswith("/@"):
                    outcome["account_menu_profile_navigation_matches"] = (
                        path == "/@" + EXPECTED
                    )
                    break
    except Exception:
        # Navigation failure is not identity evidence.
        pass
    finally:
        await page.close()
    return outcome


async def inspect_profile_without_logout(context):
    """Inspect own-profile navigation without requiring a logout item.

    Uses a disposable tab, never the user's tab. Only profile-specific
    controls in the small top-right account dropdown may be clicked.
    """
    result = {"profile_navigation_attempted": False,
              "profile_navigation_matches": False,
              "profile_owner_control_visible": False,
              "profile_login_controls_absent": False,
              "profile_menu_found": False,
              "profile_candidate_found": False,
              "profile_navigation_reached": False}
    page = await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded",
                        timeout=12000)
        await page.wait_for_timeout(1000)
        if not await open_account_menu_in_probe_page(page):
            return result
        await page.wait_for_timeout(650)
        # Classify the account dropdown by geometry. Neither names nor DOM
        # content leave the private browser; only booleans are returned.
        probe = await page.evaluate(r"""() => {
          const visible = el => {
            const r = el.getBoundingClientRect(), s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 &&
              s.display !== 'none' && s.visibility !== 'hidden';
          };
          const withinMenu = el => {
            let node = el;
            for (let i=0;i<7 && node;i++,node=node.parentElement) {
              const r = node.getBoundingClientRect();
              if (r.width >= 130 && r.width <= 440 &&
                  r.height >= 65 && r.height <= 560 &&
                  r.right >= innerWidth*.79 && r.top >= 25 &&
                  r.top <= 220 && visible(node)) return true;
            }
            return false;
          };
          const nodes = [...document.querySelectorAll(
            'a[href],button,[role="menuitem"],[role="button"],[tabindex],img'
          )].filter(el => visible(el) && withinMenu(el));
          const profile = /^(my\s*profile|view\s*profile|profile|meu\s*perfil|ver\s*perfil|perfil)$/i;
          const forbidden = /(log\s*out|logout|sign\s*out|sair|sign\s*in|login|entrar|upload|publicar|postar)/i;
          const matches = nodes.filter(el => {
            const text = (el.innerText || el.getAttribute('aria-label') || '').trim();
            if (forbidden.test(text)) return false;
            if (profile.test(text)) return true;
            if (el.tagName !== 'A') return false;
            try {
              const u = new URL(el.getAttribute('href'),location.href);
              return u.hostname === 'www.kwai.com' &&
                /^\/@[^/]+\/?$/i.test(u.pathname);
            } catch { return false; }
          });
          return {menu_found:nodes.length>0,profile_candidate_found:matches.length>0};
        }""")
        result["profile_menu_found"] = bool(probe.get("menu_found"))
        result["profile_candidate_found"] = bool(probe.get("profile_candidate_found"))
        # First use an explicitly labeled Profile item or a direct /@ link.
        clicked = await page.evaluate(r"""() => {
          const visible = el => {
            const r = el.getBoundingClientRect(), s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 &&
              s.display !== 'none' && s.visibility !== 'hidden';
          };
          const inMenu = el => {
            let n=el;
            for(let i=0;i<7 && n;i++,n=n.parentElement){
              const r=n.getBoundingClientRect();
              if(r.width>=130 && r.width<=440 && r.height>=65 &&
                 r.height<=560 && r.right>=innerWidth*.79 &&
                 r.top>=25 && r.top<=220 && visible(n))return true;
            }
            return false;
          };
          const profile=/^(my\s*profile|view\s*profile|profile|meu\s*perfil|ver\s*perfil|perfil)$/i;
          const forbidden=/(log\s*out|logout|sign\s*out|sair|sign\s*in|login|entrar|upload|publicar|postar)/i;
          const nodes=[...document.querySelectorAll(
            'a[href],button,[role="menuitem"],[role="button"],[tabindex]'
          )].filter(el=>visible(el)&&inMenu(el));
          let target=nodes.find(el=>{
            const t=(el.innerText||el.getAttribute('aria-label')||'').trim();
            return t.length<40 && profile.test(t) && !forbidden.test(t);
          });
          if(!target)target=nodes.find(el=>{
            if(el.tagName!=='A')return false;
            try {
              const u=new URL(el.getAttribute('href'),location.href);
              return u.hostname==='www.kwai.com' && /^\/@[^/]+\/?$/i.test(u.pathname);
            }catch{return false;}
          });
          if(!target)return false;
          target.click(); return true;
        }""")
        if not clicked:
            # Fallback: account-row avatar, but only within a compact
            # dropdown in the top-right and never the global header avatar.
            clicked = await page.evaluate(r"""() => {
              const visible=el=>{
                const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                return r.width>=14&&r.height>=14&&
                  s.display!=='none'&&s.visibility!=='hidden';
              };
              const imgs=[...document.querySelectorAll('img')].filter(img=>{
                const r=img.getBoundingClientRect();
                return visible(img)&&r.left>innerWidth*.68&&
                  r.top>85&&r.top<410&&r.width<=90&&r.height<=90;
              });
              for(const img of imgs){
                let row=img.parentElement;
                for(let i=0;i<5&&row;i++,row=row.parentElement){
                  const r=row.getBoundingClientRect();
                  if(r.width>=90&&r.width<=410&&r.height>=30&&
                     r.height<=110&&r.right>innerWidth*.78&&
                     r.top>70&&r.top<380){
                    const text=(row.innerText||'').trim();
                    if(/log\s*out|logout|sair|upload|publicar|postar|login/i.test(text))continue;
                    img.click();return true;
                  }
                }
              }
              return false;
            }""")
        result["profile_navigation_attempted"] = clicked is True
        if not clicked:
            return result
        for _ in range(12):
            await page.wait_for_timeout(350)
            current = urlsplit(page.url)
            if current.scheme == "https" and current.hostname == "www.kwai.com":
                path = current.path.rstrip("/").lower()
                if path.startswith("/@"):
                    result["profile_navigation_reached"] = True
                    result["profile_navigation_matches"] = path == "/@" + EXPECTED
                    break
        if result["profile_navigation_reached"]:
            owner = await page.get_by_text("Editar perfil", exact=True).count()
            owner += await page.get_by_text("Edit profile", exact=True).count()
            login = await page.get_by_text("Fazer login", exact=True).count()
            login += await page.get_by_text("Log in", exact=True).count()
            login += await page.get_by_text("Entrar", exact=True).count()
            result["profile_owner_control_visible"] = owner > 0
            result["profile_login_controls_absent"] = login == 0
    except Exception:
        pass
    finally:
        await page.close()
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
        page = await context.new_page()
        try:
            await page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(1600)
            menu_open_attempted = await open_account_menu_in_probe_page(page)
            if menu_open_attempted:
                await page.wait_for_timeout(500)
            account_menu = await inspect_open_account_menu(context)
            result["account_menu_open_attempted"] = menu_open_attempted
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
            # If the menu has no direct @handle link, follow only its avatar
            # row in a separate temporary tab to verify the real own-profile URL.
            if result["authenticated_ui_detected"] and not evidence["account_menu_profile_link_matches"]:
                navigation = await inspect_own_profile_navigation(context)
                evidence.update(navigation)
            # Independent fallback: navigate the signed-in account row even
            # when Kwai omits or hides the logout menu item.
            if not evidence["account_menu_profile_link_matches"] and not evidence.get("account_menu_profile_navigation_matches"):
                independent = await inspect_profile_without_logout(context)
                evidence.update(independent)
            result["evidence"] = evidence
            independent_owner = (
                evidence.get("profile_navigation_matches") is True
                and evidence.get("profile_owner_control_visible") is True
                and evidence.get("profile_login_controls_absent") is True
            )
            result["identity_verified"] = assess_evidence(evidence) or independent_owner
            result["authenticated_ui_detected"] = (
                result["authenticated_ui_detected"] or independent_owner
            )
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
