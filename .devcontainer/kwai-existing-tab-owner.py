#!/usr/bin/env python3
"""Fail-closed owner check on the *existing* Kwai CDP tab.

No new tab, navigation, cookie/storage read, page-text export or publishing.
Only boolean evidence is returned. The account menu may be opened in place.
"""
import re
from urllib.parse import urlsplit

EXPECTED = "universo.anthares"
KWAI_HOSTS = {"kwai.com", "www.kwai.com"}


async def inspect_existing_tab(context):
    for page in context.pages:
        url = urlsplit(page.url)
        if url.hostname not in KWAI_HOSTS:
            continue
        try:
            # Open the real account menu if closed. Never click logout or publish.
            result = await page.evaluate(r"""(expected) => {
              const visible = el => {
                if (!el) return false;
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                return r.width > 0 && r.height > 0 &&
                  s.visibility !== 'hidden' && s.display !== 'none';
              };
              const nodes = [...document.querySelectorAll('a,button,[role="button"],[role="menuitem"]')].filter(visible);
              const label = el => [
                el.innerText || '', el.getAttribute('aria-label') || '',
                el.getAttribute('title') || ''
              ].join(' ').trim();
              const logout = nodes.some(el => /^(log\s*out|logout|sair|encerrar sess[aã]o)$/i.test(label(el)));
              const loginGate = nodes.some(el => /^(log\s*in|sign\s*in|entrar|fazer login)$/i.test(label(el)));
              const menu = nodes.filter(el => el.closest('[role="menu"],[class*="menu"],[class*="popover"],[class*="dropdown"]'));
              const exact = el => {
                const href = el.getAttribute('href') || '';
                try {
                  const u = new URL(href, location.href);
                  return ['kwai.com','www.kwai.com'].includes(u.hostname) &&
                    u.pathname.replace(/\/$/,'').toLowerCase() === '/@' + expected;
                } catch (_) { return false; }
              };
              // A public link in feed content is NOT identity evidence.
              const ownLink = menu.some(el => exact(el) && visible(el));
              const accountRow = menu.some(el => exact(el) &&
                /profile|perfil|account|conta|avatar/i.test(
                  label(el) + ' ' + (el.parentElement?.className || '')));
              return {logout, loginGate, ownLink, accountRow};
            }""", EXPECTED)
            if not result["logout"]:
                # The dropdown is normally closed. Open ONLY the top-right
                # avatar with a real pointer click, never a menu action.
                points = await page.evaluate(r"""() => [...document.querySelectorAll('header img,[role="banner"] img')].filter(el => {
                    const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                    return r.width>=16 && r.width<=100 && r.height>=16 && r.height<=100 &&
                      r.left>=innerWidth*.70 && r.top<=180 &&
                      s.display!=='none' && s.visibility!=='hidden';
                  }).sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right)
                  .slice(0,1).map(el=>{const r=el.getBoundingClientRect();
                    return {x:r.left+r.width/2,y:r.top+r.height/2};})""")
                if points:
                    await page.mouse.click(points[0]["x"], points[0]["y"])
                    await page.wait_for_timeout(400)
                    result = await page.evaluate(r"""(expected) => {
                      const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                        return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
                      const nodes=[...document.querySelectorAll('a,button,[role="menuitem"],span,div')].filter(visible);
                      const logout=nodes.filter(el=>/^(log\\s*out|logout|sign\\s*out|sair)$/i.test((el.innerText||'').trim()) &&
                        (el.innerText||'').length<=32);
                      const exact=el=>{try{const u=new URL(el.getAttribute('href')||'',location.href);
                        return ['kwai.com','www.kwai.com'].includes(u.hostname)&&
                          u.pathname.replace(/\\/$/,'').toLowerCase()==='/@'+expected;}catch(_){return false}};
                      const own=logout.some(el=>{let a=el;for(let i=0;i<6&&a;i++,a=a.parentElement){
                        if(a.querySelectorAll&&[...a.querySelectorAll('a[href]')].some(exact))return true;
                      }return false});
                      const loginGate=nodes.some(el=>/^(log\\s*in|sign\\s*in|entrar|fazer login)$/i.test((el.innerText||'').trim()) &&
                        (el.innerText||'').length<=32);
                      return {logout:logout.length>0,loginGate,ownLink:own,accountRow:own};
                    }""", EXPECTED)
            if not result["logout"]:
                return {"chrome_connected": True, "authenticated_ui_detected": False,
                        "exact_owner_menu_link": False, "identity_verified": False,
                        "session_exported": False}
            exact = bool(result["ownLink"] and result["accountRow"])
            verified = bool(result["logout"] and exact and not result["loginGate"])
            return {"chrome_connected": True, "authenticated_ui_detected": bool(result["logout"]),
                    "exact_owner_menu_link": exact, "identity_verified": verified,
                    "session_exported": False}
        except Exception:
            continue
    return {"chrome_connected": True, "authenticated_ui_detected": False,
            "exact_owner_menu_link": False, "identity_verified": False,
            "session_exported": False}
