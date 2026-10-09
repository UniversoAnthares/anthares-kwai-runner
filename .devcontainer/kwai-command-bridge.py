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
COMMAND = re.compile(r"^KWAI_BRIDGE_CMD (inspect|open_home|profile_check|refresh_bridge|ui_probe|menu_probe|avatar_map|user_menu_probe|avatar_sweep|create_probe|studio_probe|mobile_cdp_probe) ([a-zA-Z0-9_-]{12,64})$")
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
            if action == "avatar_sweep":
                # Real pointer events (not DOM .click()) on up to three
                # non-link header images. Never click login/logout/upload.
                result = {"chrome_connected": True, "kwai_tab_present": False,
                          "candidate_count": 0, "pointer_clicks": 0,
                          "logout_detected": False, "profile_detected": False,
                          "navigation_changed": False, "matched_candidate_index": -1}
                for tab in list(context.pages):
                    original = tab.url
                    u = urlsplit(original)
                    if u.scheme != "https" or u.hostname != "www.kwai.com":
                        continue
                    result["kwai_tab_present"] = True
                    try:
                        coords = await tab.evaluate(r"""() => {
                          const nodes=[...document.querySelectorAll('img')].filter(el=>{
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            if(!(r.width>=16&&r.height>=16&&r.width<=100&&
                              r.height<=100&&r.left>innerWidth*.60&&r.top<200&&
                              s.display!=='none'&&s.visibility!=='hidden'&&
                              !el.closest('a[href]')))return false;
                            const parent=(el.parentElement?.innerText||'').trim();
                            return parent.length<70 &&
                              !/(upload|publicar|postar|log\s*in|sign\s*in|logout|log\s*out|sair)/i.test(parent);
                          }).sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right);
                          return nodes.slice(0,3).map(el=>{
                            const r=el.getBoundingClientRect();
                            return {x:r.left+r.width/2,y:r.top+r.height/2};
                          });
                        }""")
                        result["candidate_count"] = len(coords)
                        for index, coord in enumerate(coords):
                            await tab.mouse.move(coord["x"], coord["y"])
                            await tab.mouse.click(coord["x"], coord["y"])
                            result["pointer_clicks"] += 1
                            await tab.wait_for_timeout(550)
                            if tab.url != original:
                                result["navigation_changed"] = True
                                break
                            evidence = await tab.evaluate(r"""() => {
                              const visible=el=>{
                                const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                                return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
                              };
                              const texts=[...document.querySelectorAll(
                                'a,button,span,div,[role="menuitem"]'
                              )].filter(visible).map(el=>(el.innerText||'').trim())
                                .filter(t=>t.length<=40);
                              return {
                                logout:texts.some(t=>/^(log\s*out|logout|sign\s*out|sair)$/i.test(t)),
                                profile:texts.some(t=>/^(my\s*profile|view\s*profile|profile|meu\s*perfil|ver\s*perfil|perfil)$/i.test(t))
                              };
                            }""")
                            if evidence.get("logout") or evidence.get("profile"):
                                result["logout_detected"] = bool(evidence.get("logout"))
                                result["profile_detected"] = bool(evidence.get("profile"))
                                result["matched_candidate_index"] = index
                                break
                            # Close any opened dropdown before trying another
                            # candidate; the next click must not hit an overlay.
                            await tab.mouse.click(12, 220)
                        if tab.url == original:
                            await tab.mouse.click(12, 220)
                    except Exception:
                        pass
                    break
                return result
            if action == "user_menu_probe":
                # Target the unique top-right account/user-class control
                # instead of the rightmost image, which may be unrelated.
                result = {"chrome_connected": True, "kwai_tab_present": False,
                          "user_class_candidate_found": False,
                          "user_class_clicked": False,
                          "logout_visible_after_click": False,
                          "profile_control_after_click": False,
                          "menu_after_click": False}
                for tab in list(context.pages):
                    u = urlsplit(tab.url)
                    if u.scheme != "https" or u.hostname != "www.kwai.com":
                        continue
                    result["kwai_tab_present"] = True
                    try:
                        clicked = await tab.evaluate(r"""() => {
                          const els=[...document.querySelectorAll('[class*="user" i]')]
                            .filter(el=>{
                              const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                              return r.width>=12&&r.height>=12&&r.width<=240&&
                                r.height<=160&&r.left>innerWidth*.65&&r.top<200&&
                                s.display!=='none'&&s.visibility!=='hidden'&&
                                !el.closest('a[href]');
                            }).sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right);
                          if(!els.length)return {found:false,clicked:false};
                          els[0].click();return {found:true,clicked:true};
                        }""")
                        result["user_class_candidate_found"] = bool(clicked.get("found"))
                        result["user_class_clicked"] = bool(clicked.get("clicked"))
                        if not result["user_class_clicked"]:
                            break
                        await tab.wait_for_timeout(600)
                        after = await tab.evaluate(r"""() => {
                          const visible=el=>{
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
                          };
                          const texts=[...document.querySelectorAll(
                            'a,button,span,[role="menuitem"],[role="button"]'
                          )].filter(visible).map(el=>(el.innerText||'').trim())
                            .filter(t=>t.length<=40);
                          return {
                            logout:texts.some(t=>/^(log\s*out|logout|sign\s*out|sair)$/i.test(t)),
                            profile:texts.some(t=>/^(my\s*profile|view\s*profile|profile|meu\s*perfil|ver\s*perfil|perfil)$/i.test(t)),
                            menu:!![...document.querySelectorAll('[role="menu"],[data-testid*="account"],[data-testid*="user-menu"]')].find(visible)
                          };
                        }""")
                        result["logout_visible_after_click"] = bool(after.get("logout"))
                        result["profile_control_after_click"] = bool(after.get("profile"))
                        result["menu_after_click"] = bool(after.get("menu"))
                        if tab.url == u.geturl():
                            await tab.evaluate(r"""() => {
                              const el=[...document.querySelectorAll('[class*="user" i]')]
                                .find(e=>{const r=e.getBoundingClientRect();
                                  return r.width>=12&&r.height>=12&&r.width<=240&&
                                    r.height<=160&&r.left>innerWidth*.65&&r.top<200&&
                                    !e.closest('a[href]')});
                              if(el)el.click();
                            }""")
                    except Exception:
                        pass
                    break
                return result
            if action == "avatar_map":
                # Count-only map of possible account triggers in the visible
                # header; does not read labels, text, attributes or URLs.
                result = {"chrome_connected": True, "kwai_tab_present": False}
                for tab in list(context.pages):
                    u = urlsplit(tab.url)
                    if u.scheme != "https" or u.hostname != "www.kwai.com":
                        continue
                    result["kwai_tab_present"] = True
                    try:
                        flags = await tab.evaluate(r"""() => {
                          const topRight = el => {
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            return r.width>=10&&r.height>=10&&r.left>innerWidth*.60&&
                              r.top>=0&&r.top<230&&s.display!=='none'&&
                              s.visibility!=='hidden';
                          };
                          const count=selector=>Math.min(20,
                            [...document.querySelectorAll(selector)].filter(topRight).length);
                          return {
                            top_right_images:count('img'),
                            top_right_buttons:count('button'),
                            top_right_roles:count('[role="button"]'),
                            top_right_links:count('a[href]'),
                            top_right_avatar_class:count('[class*="avatar" i]'),
                            top_right_user_class:count('[class*="user" i]'),
                            top_right_account_label:count('[aria-label*="account" i]'),
                            top_right_profile_label:count('[aria-label*="profile" i]'),
                            top_right_user_label:count('[aria-label*="user" i]'),
                            top_right_user_testid:count('[data-testid*="user" i]'),
                            top_right_pointer:Math.min(20,[...document.querySelectorAll(
                              'div,span,svg,button,img'
                            )].filter(el=>topRight(el)&&getComputedStyle(el).cursor==='pointer').length)
                          };
                        }""")
                        for key, val in flags.items():
                            if isinstance(val, int) and not isinstance(val, bool):
                                result[key] = min(20, max(0, val))
                    except Exception:
                        result["ui_inspection_failed"] = True
                    break
                return result
            if action == "menu_probe":
                # UI-only test on the already-open Kwai tab. It never reads
                # secrets, changes routes, or clicks a logout/login control.
                result = {"chrome_connected": True, "kwai_existing_tab_present": False,
                          "existing_avatar_candidate": False,
                          "existing_avatar_clicked": False,
                          "existing_menu_visible": False,
                          "existing_logout_visible": False,
                          "existing_profile_candidate": False,
                          "existing_login_visible": False}
                for tab in list(context.pages):
                    u = urlsplit(tab.url)
                    if u.scheme != "https" or u.hostname != "www.kwai.com":
                        continue
                    result["kwai_existing_tab_present"] = True
                    try:
                        before = await tab.evaluate(r"""() => {
                          const visible=el=>{
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
                          };
                          const nodes=[...document.querySelectorAll('a,button,[role="menuitem"],span,div')]
                            .filter(visible);
                          const logout=nodes.some(n=>{const t=(n.innerText||'').trim();return t.length<=32&&/^(log\s*out|logout|sign\s*out|sair)$/i.test(t)});
                          return {logout};
                        }""")
                        if before.get("logout"):
                            result["existing_menu_visible"] = True
                            result["existing_logout_visible"] = True
                            break
                        clicked = await tab.evaluate(r"""() => {
                          const visible=el=>{
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            return r.width>=16&&r.height>=16&&r.width<=100&&r.height<=100&&
                              s.display!=='none'&&s.visibility!=='hidden';
                          };
                          const imgs=[...document.querySelectorAll(
                            'header img,[role="banner"] img,img,[aria-label*="avatar" i],[data-testid*="avatar" i]'
                          )].filter(el=>{
                            const r=el.getBoundingClientRect();
                            return visible(el)&&r.left>innerWidth*.7&&r.top<180&&
                              !el.closest('a[href]');
                          }).sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right);
                          if(!imgs.length)return {candidate:false,clicked:false};
                          imgs[0].click();return {candidate:true,clicked:true};
                        }""")
                        result["existing_avatar_candidate"] = bool(clicked.get("candidate"))
                        result["existing_avatar_clicked"] = bool(clicked.get("clicked"))
                        if not result["existing_avatar_clicked"]:
                            break
                        await tab.wait_for_timeout(650)
                        after = await tab.evaluate(r"""() => {
                          const visible=el=>{
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
                          };
                          const nodes=[...document.querySelectorAll(
                            'a,button,[role="menuitem"],[role="button"],span,div'
                          )].filter(visible);
                          const texts=nodes.map(n=>(n.innerText||'').trim()).filter(t=>t.length<=40);
                          const logout=texts.some(t=>/^(log\s*out|logout|sign\s*out|sair)$/i.test(t));
                          const login=texts.some(t=>/^(log\s*in|sign\s*in|entrar|fazer login)$/i.test(t));
                          const profile=texts.some(t=>/^(my\s*profile|view\s*profile|profile|meu\s*perfil|ver\s*perfil|perfil)$/i.test(t));
                          return {logout,login,profile,menu:!!document.querySelector(
                            '[role="menu"],[data-testid*="account"],[data-testid*="user-menu"]'
                          )};
                        }""")
                        result["existing_menu_visible"] = bool(after.get("menu")) or bool(after.get("logout"))
                        result["existing_logout_visible"] = bool(after.get("logout"))
                        result["existing_login_visible"] = bool(after.get("login"))
                        result["existing_profile_candidate"] = bool(after.get("profile"))
                        # Restore the UI by toggling the same non-link avatar.
                        if tab.url == u.geturl():
                            await tab.evaluate(r"""() => {
                              const imgs=[...document.querySelectorAll('img')].filter(el=>{
                                const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                                return r.width>=16&&r.height>=16&&r.width<=100&&r.height<=100&&
                                  r.left>innerWidth*.7&&r.top<180&&
                                  s.display!=='none'&&s.visibility!=='hidden'&&
                                  !el.closest('a[href]');
                              }).sort((a,b)=>b.getBoundingClientRect().right-a.getBoundingClientRect().right);
                              if(imgs.length)imgs[0].click();
                            }""")
                    except Exception:
                        pass
                    break
                return result
            if action == "ui_probe":
                # Read-only sanitized UI diagnostics from the EXISTING tabs.
                # No DOM text, URL, username, cookie, or screenshot is returned.
                summary = {
                    "chrome_connected": True,
                    "kwai_existing_tab_count": 0,
                    "kwai_existing_app_loaded": False,
                    "kwai_existing_header_avatar": False,
                    "kwai_existing_logout_visible": False,
                    "kwai_existing_login_visible": False,
                    "kwai_existing_profile_link": False,
                    "kwai_existing_owner_edit": False,
                    "kwai_existing_expected_profile_route": False,
                    "kwai_existing_document_complete": False,
                    "kwai_existing_body_nonempty": False,
                    "kwai_existing_has_next_root": False,
                    "kwai_existing_known_display_name_visible": False,
                    "kwai_existing_has_signin_wall": False,
                    "kwai_existing_candidate_inside_button": False,
                }
                for tab in list(context.pages):
                    u = urlsplit(tab.url)
                    if u.scheme != "https" or u.hostname != "www.kwai.com":
                        continue
                    summary["kwai_existing_tab_count"] += 1
                    try:
                        flags = await tab.evaluate(r"""() => {
                          const visible = el => {
                            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                            return r.width>0 && r.height>0 &&
                              s.display!=='none' && s.visibility!=='hidden';
                          };
                          const nodes=[...document.querySelectorAll('a,button,span,[role="menuitem"],[role="button"]')]
                            .filter(visible);
                          const texts=nodes.map(n=>(n.innerText||'').trim()).filter(t=>t.length<=40);
                          const images=[...document.querySelectorAll('img,[aria-label*="avatar" i]')];
                          return {
                            app_loaded: !!document.querySelector('main,header,[id="root"],[id="app"]'),
                            header_avatar: images.some(n=>{const r=n.getBoundingClientRect();return visible(n)&&r.left>=innerWidth*.7&&r.top<200&&r.width<=100&&r.height<=100;}),
                            logout_visible:texts.some(t=>/^(log\s*out|logout|sign\s*out|sair)$/i.test(t)),
                            login_visible:texts.some(t=>/^(log\s*in|sign\s*in|entrar|fazer login)$/i.test(t)),
                            profile_link:[...document.querySelectorAll('a[href]')].some(n=>{try{const u=new URL(n.getAttribute('href'),location.href);return u.hostname==='www.kwai.com'&&/^\/@[^/]+\/?$/i.test(u.pathname)}catch{return false}}),
                            owner_edit:texts.some(t=>/^(edit profile|editar perfil)$/i.test(t)),
                            document_complete:document.readyState==='complete',
                            body_nonempty:(document.body?.innerText||'').trim().length>50,
                            has_next_root:!!document.querySelector('#__next,[data-reactroot],#__nuxt'),
                            known_display_name_visible:(document.body?.innerText||'').includes('Lucas Rosalem'),
                            has_signin_wall:/please\s*(log\s*in|sign\s*in)|faça\s*login\s*para/i.test((document.body?.innerText||'').slice(0,4000)),
                            candidate_inside_button:images.some(n=>{
                              const r=n.getBoundingClientRect();
                              return visible(n)&&r.left>=innerWidth*.7&&r.top<200&&
                                !!n.closest('button,[role="button"]');
                            })
                          };
                        }""")
                        summary["kwai_existing_app_loaded"] |= bool(flags.get("app_loaded"))
                        summary["kwai_existing_header_avatar"] |= bool(flags.get("header_avatar"))
                        summary["kwai_existing_logout_visible"] |= bool(flags.get("logout_visible"))
                        summary["kwai_existing_login_visible"] |= bool(flags.get("login_visible"))
                        summary["kwai_existing_profile_link"] |= bool(flags.get("profile_link"))
                        summary["kwai_existing_owner_edit"] |= bool(flags.get("owner_edit"))
                        summary["kwai_existing_document_complete"] |= bool(flags.get("document_complete"))
                        summary["kwai_existing_body_nonempty"] |= bool(flags.get("body_nonempty"))
                        summary["kwai_existing_has_next_root"] |= bool(flags.get("has_next_root"))
                        summary["kwai_existing_known_display_name_visible"] |= bool(flags.get("known_display_name_visible"))
                        summary["kwai_existing_has_signin_wall"] |= bool(flags.get("has_signin_wall"))
                        summary["kwai_existing_candidate_inside_button"] |= bool(flags.get("candidate_inside_button"))
                        summary["kwai_existing_expected_profile_route"] |= (
                            u.path.rstrip("/").lower() == "/@universo.anthares"
                        )
                    except Exception:
                        continue
                return summary
            if action == "studio_probe":
                # Fixed-origin, disposable-tab Studio inspection. The current
                # Kwai tabs and private browser profile remain untouched.
                import importlib.util
                probe_path = Path(__file__).with_name("kwai-create-surface-probe.py")
                spec = importlib.util.spec_from_file_location(
                    "kwai_create_surface_probe", probe_path
                )
                probe = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(probe)
                tab = await context.new_page()
                reached = False
                studio_host = False
                try:
                    await tab.goto(
                        "https://studio.kwai.com/",
                        wait_until="domcontentloaded",
                        timeout=12000,
                    )
                    await tab.wait_for_timeout(1100)
                    reached = True
                    studio_host = urlsplit(tab.url).hostname == "studio.kwai.com"
                    flags = await probe.inspect_existing_pages(context)
                    return {
                        "chrome_connected": True,
                        "studio_navigation_reached": reached,
                        "studio_host_reached": studio_host,
                        "studio_tab_temporary": True,
                        **flags,
                    }
                except Exception:
                    return {
                        "chrome_connected": True,
                        "studio_navigation_reached": reached,
                        "studio_host_reached": studio_host,
                        "studio_tab_temporary": True,
                        "operational_create_surface": False,
                        "read_only_probe": True,
                        "studio_probe_failed": True,
                    }
                finally:
                    await tab.close()
            if action == "mobile_cdp_probe":
                # A temporary page uses Android UA, mobile client hints,
                # touch and device metrics, scoped to that CDP target.
                # Existing tabs and authenticated Chrome profile are unchanged.
                import importlib.util
                probe_path = Path(__file__).with_name("kwai-mobile-cdp-probe.py")
                spec = importlib.util.spec_from_file_location(
                    "kwai_mobile_cdp_probe", probe_path
                )
                probe = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(probe)
                return {"chrome_connected": True,
                        **(await probe.probe_mobile_client(context))}
            if action == "create_probe":
                # Reuse the tested, read-only classifier on existing tabs.
                # No navigation, clicks, upload, or account/session extraction.
                import importlib.util
                probe_path = Path(__file__).with_name("kwai-create-surface-probe.py")
                spec = importlib.util.spec_from_file_location(
                    "kwai_create_surface_probe", probe_path
                )
                probe = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(probe)
                flags = await probe.inspect_existing_pages(context)
                return {"chrome_connected": True, **flags}
            if action == "profile_check":
                # Reuse the tested private guard rather than searching a closed
                # menu in an arbitrary Kwai tab (known false-negative).
                import importlib.util
                guard_path = Path(__file__).with_name("kwai-identity-guard.py")
                spec = importlib.util.spec_from_file_location("kwai_identity_guard", guard_path)
                guard = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(guard)
                # The guard creates disposable tabs, opens the account menu,
                # follows only the own-profile avatar and closes its probes.
                # Return booleans only; no names, handles, URLs or page content.
                evidence = await guard.inspect_browser()
                flags = evidence.get("evidence") or {}
                return {
                    "chrome_connected": bool(evidence.get("chrome_connected")),
                    "profile_check": "complete",
                    "authenticated_ui_detected": bool(evidence.get("authenticated_ui_detected")),
                    "identity_verified": bool(evidence.get("identity_verified")),
                    "account_menu_open_attempted": bool(evidence.get("account_menu_open_attempted")),
                    "logout_visible": bool(flags.get("account_menu_logout_visible")),
                    "profile_navigation_attempted": bool(flags.get("account_menu_profile_navigation_attempted")),
                    "profile_popup_opened": bool(flags.get("account_menu_profile_popup_opened")),
                    "profile_route_reached": bool(flags.get("account_menu_profile_route_reached")),
                    "profile_route_changed": bool(flags.get("account_menu_profile_route_changed")),
                    "profile_owner_edit_visible": bool(flags.get("account_menu_profile_owner_edit_visible")),
                    "profile_handle_text_matches": bool(flags.get("account_menu_profile_handle_text_matches")),
                    "independent_profile_navigation_attempted": bool(flags.get("profile_navigation_attempted")),
                    "profile_menu_found": bool(flags.get("profile_menu_found")),
                    "profile_candidate_found": bool(flags.get("profile_candidate_found")),
                    "profile_navigation_reached": bool(flags.get("profile_navigation_reached")),
                    "independent_profile_matches": bool(flags.get("profile_navigation_matches")),
                    "owner_edit_control_visible": bool(flags.get("profile_owner_control_visible")),
                    "own_profile_matches_expected": bool(flags.get("account_menu_profile_navigation_matches")
                                                         or flags.get("account_menu_profile_link_matches")
                                                         or flags.get("profile_navigation_matches")),
                    "persistence_permitted": False,
                    "server_identity_verified": False,
                }
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
    print("KWAI_BRIDGE_READY=issue-12;commands=inspect,open_home,profile_check,refresh_bridge,ui_probe,menu_probe,avatar_map,user_menu_probe,avatar_sweep,create_probe,studio_probe,mobile_cdp_probe;no_session_export", flush=True)
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
                if action == "refresh_bridge":
                    # Only the owner may request a fast-forward of the fixed
                    # main branch. No arbitrary shell command is accepted.
                    checkout = Path(__file__).resolve().parent.parent
                    pull = subprocess.run(
                        ["git", "pull", "--ff-only", "origin", "main"],
                        cwd=checkout, capture_output=True, text=True, timeout=35,
                    )
                    outcome = {"nonce": nonce, "status": "ok" if pull.returncode == 0 else "error",
                               "refresh_started": pull.returncode == 0,
                               "chrome_profile_untouched": True}
                else:
                    try:
                        result = asyncio.run(browser_action(action))
                        outcome = {"nonce": nonce, "status": "ok", **result}
                    except Exception:
                        outcome = {"nonce": nonce, "status": "error", "reason": "chrome_unavailable_or_navigation_failed"}
                gh("POST", f"repos/{REPO}/issues/{ISSUE}/comments", {"body": "KWAI_BRIDGE_RESULT " + json.dumps(outcome, sort_keys=True)})
                if action == "refresh_bridge" and outcome["status"] == "ok":
                    # Run after posting acknowledgement; this will replace
                    # only the bridge process, not Chrome or its private state.
                    log_path = STATE.parent / "bridge-refresh.log"
                    with log_path.open("ab") as log:
                        subprocess.Popen(
                            ["bash", ".devcontainer/kwai-start.sh"],
                            cwd=checkout, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    return
        except Exception:
            print("KWAI_BRIDGE_POLL_RETRY", flush=True)
        time.sleep(8)

if __name__ == "__main__":
    main()
