#!/usr/bin/env python3
"""Fail-closed exact-owner verification for the live Kwai Chrome session.

No cookies, storage, tokens, screenshots, page text, or credentials leave Chrome.
Only boolean evidence is returned. Publication is never attempted here.
"""
import importlib.util
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED = "universo.anthares"
KWAI_HOSTS = {"kwai.com", "www.kwai.com"}


def load_guard():
    path = Path(__file__).with_name("kwai-identity-guard.py")
    spec = importlib.util.spec_from_file_location("kwai_identity_guard_owner_fallback", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def inspect_menu(page):
    """Return only boolean account-menu evidence from one existing Kwai tab."""
    return await page.evaluate(r"""(expected) => {
      const visible = el => {
        if (!el) return false;
        const r = el.getBoundingClientRect(), s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.display !== 'none' &&
          s.visibility !== 'hidden';
      };
      const nodes = [...document.querySelectorAll(
        'a[href],button,[role="button"],[role="menuitem"],span,div'
      )].filter(visible);
      const logoutRe = /^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o|encerrar sess[aã]o)$/i;
      const loginRe = /^(log\s*in|sign\s*in|login|entrar|fazer login)$/i;
      const text = el => (el.innerText || el.textContent || '').trim();
      const logout = nodes.find(el => text(el).length <= 40 && logoutRe.test(text(el)));
      const loginGate = nodes.some(el => text(el).length <= 40 && loginRe.test(text(el)));
      if (!logout) return {logout:false, loginGate, exactHref:false, exactText:false};

      let panel = logout;
      for (let i = 0; i < 8 && panel; i++, panel = panel.parentElement) {
        const r = panel.getBoundingClientRect();
        if (!visible(panel) || r.width < 100 || r.width > 520 ||
            r.height < 50 || r.height > 700 || r.right < innerWidth * .65) continue;

        const exactHref = [...panel.querySelectorAll('a[href]')].some(a => {
          try {
            const u = new URL(a.getAttribute('href'), location.href);
            return ['kwai.com','www.kwai.com'].includes(u.hostname) &&
              u.pathname.replace(/\/$/, '').toLowerCase() === '/@' + expected;
          } catch (_) { return false; }
        });
        const tokens = [...panel.querySelectorAll('a,span,div,button,[role="menuitem"]')]
          .filter(visible)
          .flatMap(el => text(el).split(/\s+/))
          .map(t => t.replace(/^[,;|]+|[,;|]+$/g, '').toLowerCase());
        const exactText = tokens.includes('@' + expected) || tokens.includes(expected);
        if (exactHref || exactText) {
          return {logout:true, loginGate, exactHref, exactText};
        }
      }
      return {logout:true, loginGate, exactHref:false, exactText:false};
    }""", EXPECTED)


async def inspect_existing_tab(context):
    guard = load_guard()
    authenticated = False
    exact_href = False
    exact_text = False

    # First inspect the user's existing Kwai tabs. If the menu is closed, use
    # the already-hardened pointer routine from the identity guard to open only
    # the top-right account trigger; never click Log out or Publish.
    for page in list(context.pages):
        url = urlsplit(page.url)
        if url.hostname not in KWAI_HOSTS:
            continue
        try:
            evidence = await inspect_menu(page)
            if not evidence["logout"]:
                await guard.open_account_menu_in_probe_page(page)
                await page.wait_for_timeout(500)
                evidence = await inspect_menu(page)
            authenticated |= bool(evidence["logout"] and not evidence["loginGate"])
            exact_href |= bool(evidence["exactHref"])
            exact_text |= bool(evidence["exactText"])
            if authenticated and (exact_href or exact_text):
                return {
                    "chrome_connected": True,
                    "authenticated_ui_detected": True,
                    "exact_owner_menu_link": exact_href,
                    "exact_owner_menu_text": exact_text,
                    "exact_owner_navigation": False,
                    "identity_verified": True,
                    "session_exported": False,
                }
        except Exception:
            continue

    # Fallback 1: from an authenticated menu, follow only the account row in a
    # disposable tab and accept an exact /@universo.anthares destination.
    navigation = await guard.inspect_own_profile_navigation(context)
    exact_navigation = bool(navigation.get("account_menu_profile_navigation_matches"))
    if exact_navigation:
        return {
            "chrome_connected": True,
            "authenticated_ui_detected": True,
            "exact_owner_menu_link": exact_href,
            "exact_owner_menu_text": exact_text,
            "exact_owner_navigation": True,
            "identity_verified": True,
            "session_exported": False,
        }

    # Fallback 2: modern Kwai variants may omit Log out from the compact menu.
    # In that case require exact own-profile navigation PLUS owner-only profile
    # control and absence of login controls; this remains fail-closed.
    independent = await guard.inspect_profile_without_logout(context)
    independent_owner = bool(
        independent.get("profile_navigation_matches") is True
        and independent.get("profile_owner_control_visible") is True
        and independent.get("profile_login_controls_absent") is True
    )
    return {
        "chrome_connected": True,
        "authenticated_ui_detected": bool(authenticated or independent_owner),
        "exact_owner_menu_link": exact_href,
        "exact_owner_menu_text": exact_text,
        "exact_owner_navigation": bool(exact_navigation or independent_owner),
        "identity_verified": independent_owner,
        "session_exported": False,
    }
