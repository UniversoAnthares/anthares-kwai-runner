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
COMMAND = re.compile(r"^KWAI_BRIDGE_CMD (inspect|open_home|profile_check|refresh_bridge|ui_probe|menu_probe) ([a-zA-Z0-9_-]{12,64})$")
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
                            owner_edit:texts.some(t=>/^(edit profile|editar perfil)$/i.test(t))
                          };
                        }""")
                        summary["kwai_existing_app_loaded"] |= bool(flags.get("app_loaded"))
                        summary["kwai_existing_header_avatar"] |= bool(flags.get("header_avatar"))
                        summary["kwai_existing_logout_visible"] |= bool(flags.get("logout_visible"))
                        summary["kwai_existing_login_visible"] |= bool(flags.get("login_visible"))
                        summary["kwai_existing_profile_link"] |= bool(flags.get("profile_link"))
                        summary["kwai_existing_owner_edit"] |= bool(flags.get("owner_edit"))
                        summary["kwai_existing_expected_profile_route"] |= (
                            u.path.rstrip("/").lower() == "/@universo.anthares"
                        )
                    except Exception:
                        continue
                return summary
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
    print("KWAI_BRIDGE_READY=issue-12;commands=inspect,open_home,profile_check,refresh_bridge,ui_probe,menu_probe;no_session_export", flush=True)
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
