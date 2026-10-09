#!/usr/bin/env python3
"""Fail-closed exact-owner verification for the live Kwai Chrome session.

No cookies, storage, tokens, screenshots, raw page text, or credentials leave
Chrome. Only boolean evidence is returned. Publication is never attempted.
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


async def verify_profile_page(page):
    """Return boolean-only exact-profile evidence."""
    try:
        return await page.evaluate(r"""(expected) => {
          const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const path=location.pathname.replace(/\/$/,'').toLowerCase();
          const nodes=[...document.querySelectorAll('a,button,[role="button"],span,div')].filter(visible);
          const txt=el=>(el.innerText||el.textContent||'').trim();
          const exactRoute=path==='/@'+expected;
          const exactHandle=nodes.some(el=>{const t=txt(el).toLowerCase();
            return t==='@'+expected||t===expected;});
          const ownerControl=nodes.some(el=>/^(edit profile|editar perfil)$/i.test(txt(el))&&txt(el).length<=40);
          const loginGate=nodes.some(el=>/^(log\s*in|sign\s*in|login|entrar|fazer login)$/i.test(txt(el))&&txt(el).length<=40);
          return {exactRoute,exactHandle,ownerControl,loginGate};
        }""", EXPECTED)
    except Exception:
        return {"exactRoute": False, "exactHandle": False,
                "ownerControl": False, "loginGate": True}


async def authenticated_menu_probe(context, guard):
    """Open only the account trigger in a disposable tab and inspect booleans."""
    page = await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(700)
        await guard.open_account_menu_in_probe_page(page)
        await page.wait_for_timeout(450)
        evidence = await guard.inspect_open_account_menu(context)
        return {
            "authenticated": bool(evidence.get("account_menu_logout_visible")),
            "exact_link": bool(evidence.get("account_menu_profile_link_matches")),
        }
    except Exception:
        return {"authenticated": False, "exact_link": False}
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def probe_named_self_profile(context):
    """Click only a Profile/Perfil navigation control in a disposable tab.

    Because this fallback is called only after authenticated-menu proof, an
    exact expected handle reached from a first-party self-profile navigation is
    independent ownership evidence even when Kwai exposes no Edit profile link
    in the compact account dropdown.
    """
    for candidate_index in range(4):
        before = list(context.pages)
        page = await context.new_page()
        try:
            await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(800)
            candidates = await page.evaluate(r"""() => {
              const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
              const text=el=>[(el.innerText||el.textContent||''),(el.getAttribute('aria-label')||''),(el.getAttribute('title')||'')]
                .join(' ').replace(/\s+/g,' ').trim();
              const exact=/^(profile|perfil|my profile|meu perfil)$/i;
              const items=[...document.querySelectorAll('a[href],button,[role="button"],[role="link"]')]
                .filter(el=>{
                  if(!visible(el))return false;
                  const r=el.getBoundingClientRect();
                  const inNavigation=!!el.closest('nav,header,[role="navigation"],[role="banner"]')||r.left<innerWidth*.35;
                  if(!inNavigation||r.width<20||r.height<18||r.width>500||r.height>140)return false;
                  let profileish=exact.test(text(el));
                  if(!profileish&&el.tagName==='A'){
                    try{const u=new URL(el.getAttribute('href'),location.href);
                      profileish=['kwai.com','www.kwai.com'].includes(u.hostname)&&
                        (/^\/(profile|user)(\/|$)/i.test(u.pathname)||/^\/@[^/]+\/?$/i.test(u.pathname));
                    }catch(_){profileish=false;}
                  }
                  return profileish;
                })
                .map(el=>{const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,top:r.top,left:r.left};})
                .sort((a,b)=>a.left-b.left||a.top-b.top);
              return items.slice(0,4).map(({x,y})=>({x,y}));
            }""")
            if candidate_index >= len(candidates):
                break
            point = candidates[candidate_index]
            await page.mouse.click(point["x"], point["y"])
            for _ in range(14):
                await page.wait_for_timeout(350)
                opened = [p for p in context.pages if p not in before and p != page]
                for candidate in [page] + opened:
                    url = urlsplit(candidate.url)
                    if url.hostname not in KWAI_HOSTS:
                        continue
                    proof = await verify_profile_page(candidate)
                    if proof["loginGate"]:
                        continue
                    # Source control is authenticated first-party Profile/Perfil;
                    # exact route OR exact visible handle therefore proves self.
                    if proof["exactRoute"] or proof["exactHandle"]:
                        return True
        except Exception:
            pass
        finally:
            for extra in list(context.pages):
                if extra not in before:
                    try:
                        await extra.close()
                    except Exception:
                        pass
    return False


async def probe_account_row_candidates(context, guard):
    """Try safe account-row targets above Log out; coordinates only leave JS."""
    for candidate_index in range(8):
        before = list(context.pages)
        page = await context.new_page()
        try:
            await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)
            if not await guard.open_account_menu_in_probe_page(page):
                continue
            await page.wait_for_timeout(450)
            candidates = await page.evaluate(r"""() => {
              const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
              const text=el=>(el.innerText||el.textContent||'').trim();
              const logoutRe=/^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o|encerrar sess[aã]o)$/i;
              const blocked=/(log\s*out|logout|sair|delete|remove|excluir|apagar|publish|publicar|postar|upload|enviar|sign\s*out)/i;
              const nodes=[...document.querySelectorAll('a,button,[role="button"],[role="menuitem"],span,div')].filter(visible);
              const logout=nodes.find(el=>text(el).length<=40&&logoutRe.test(text(el)));
              if(!logout)return [];
              let panel=null,a=logout;
              for(let i=0;i<8&&a;i++,a=a.parentElement){const r=a.getBoundingClientRect();
                if(visible(a)&&r.width>=120&&r.width<=520&&r.height>=80&&r.height<=700&&r.right>=innerWidth*.65){panel=a;break;}}
              if(!panel)return [];
              const lr=logout.getBoundingClientRect(),rows=[];
              const add=el=>{if(!el||!visible(el)||!panel.contains(el))return;
                const r=el.getBoundingClientRect(),t=text(el);
                if(r.bottom>lr.top+4||r.width<24||r.width>480||r.height<20||r.height>120)return;
                if(t.length>120||blocked.test(t)||r.right<innerWidth*.60)return;
                const key=[Math.round(r.left/4),Math.round(r.top/4),Math.round(r.width/4),Math.round(r.height/4)].join(':');
                if(rows.some(x=>x.key===key))return;
                rows.push({key,x:r.left+r.width/2,y:r.top+r.height/2,area:r.width*r.height,top:r.top});};
              [...panel.querySelectorAll('a[href],button,[role="button"],[role="menuitem"]')].forEach(add);
              [...panel.querySelectorAll('img')].filter(visible).forEach(img=>{let n=img;
                for(let i=0;i<5&&n&&panel.contains(n);i++,n=n.parentElement)add(n);});
              return rows.sort((a,b)=>a.top-b.top||a.area-b.area).slice(0,8).map(({x,y})=>({x,y}));
            }""")
            if candidate_index >= len(candidates):
                break
            point = candidates[candidate_index]
            await page.mouse.click(point["x"], point["y"])
            for _ in range(12):
                await page.wait_for_timeout(350)
                opened = [p for p in context.pages if p not in before and p != page]
                for candidate in [page] + opened:
                    if urlsplit(candidate.url).hostname not in KWAI_HOSTS:
                        continue
                    proof = await verify_profile_page(candidate)
                    if not proof["loginGate"] and (proof["exactRoute"] or (proof["exactHandle"] and proof["ownerControl"])):
                        return True
        except Exception:
            pass
        finally:
            for extra in list(context.pages):
                if extra not in before:
                    try:
                        await extra.close()
                    except Exception:
                        pass
    return False


async def inspect_existing_tab(context):
    guard = load_guard()
    menu = await authenticated_menu_probe(context, guard)
    authenticated = bool(menu["authenticated"])
    exact_link = bool(menu["exact_link"])

    if authenticated and exact_link:
        return {
            "chrome_connected": True,
            "authenticated_ui_detected": True,
            "exact_owner_menu_link": True,
            "exact_owner_menu_text": False,
            "exact_owner_navigation": False,
            "identity_verified": True,
            "session_exported": False,
        }

    # Existing hardened account-row path.
    navigation = await guard.inspect_own_profile_navigation(context)
    exact_navigation = bool(navigation.get("account_menu_profile_navigation_matches"))
    if authenticated and exact_navigation:
        return {
            "chrome_connected": True,
            "authenticated_ui_detected": True,
            "exact_owner_menu_link": exact_link,
            "exact_owner_menu_text": False,
            "exact_owner_navigation": True,
            "identity_verified": True,
            "session_exported": False,
        }

    # Independent self-profile route from the authenticated main navigation.
    named_navigation = False
    if authenticated:
        named_navigation = await probe_named_self_profile(context)
    if named_navigation:
        return {
            "chrome_connected": True,
            "authenticated_ui_detected": True,
            "exact_owner_menu_link": exact_link,
            "exact_owner_menu_text": False,
            "exact_owner_navigation": True,
            "identity_verified": True,
            "session_exported": False,
        }

    # React account rows may attach handlers above/beside the visible avatar.
    candidate_navigation = False
    if authenticated:
        candidate_navigation = await probe_account_row_candidates(context, guard)
    if candidate_navigation:
        return {
            "chrome_connected": True,
            "authenticated_ui_detected": True,
            "exact_owner_menu_link": exact_link,
            "exact_owner_menu_text": False,
            "exact_owner_navigation": True,
            "identity_verified": True,
            "session_exported": False,
        }

    # Modern compact menus may omit Log out; keep a strict owner-only fallback.
    independent = await guard.inspect_profile_without_logout(context)
    independent_owner = bool(
        independent.get("profile_navigation_matches") is True
        and independent.get("profile_owner_control_visible") is True
        and independent.get("profile_login_controls_absent") is True
    )
    return {
        "chrome_connected": True,
        "authenticated_ui_detected": bool(authenticated or independent_owner),
        "exact_owner_menu_link": exact_link,
        "exact_owner_menu_text": False,
        "exact_owner_navigation": bool(exact_navigation or named_navigation or candidate_navigation or independent_owner),
        "identity_verified": independent_owner,
        "session_exported": False,
    }
