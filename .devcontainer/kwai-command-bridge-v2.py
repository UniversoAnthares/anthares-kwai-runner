#!/usr/bin/env python3
"""Owner-only Codespaces bridge that polls newest issue comments.

It never exports cookies, storage, tokens, page text, or screenshots. Browser
mutations are limited to disposable probe tabs and an explicit publisher phase.
"""
import asyncio
import importlib.util
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

REPO = "UniversoAnthares/anthares-kwai-runner"
ISSUE = 12
OWNER = "universoanthares"
EXPECTED = "lucasrosalem"
STATE = Path.home() / ".kwai-remote-private" / "bridge-v2-seen.json"
COMMAND = re.compile(r"^KWAI_BRIDGE_CMD (inspect|refresh_bridge|profile_check|owner_probe|create_probe|mobile_cdp_probe) ([a-zA-Z0-9_-]{12,64})$")


def gh(method, endpoint, data=None):
    args = ["gh", "api", "--method", method, endpoint]
    if data is not None:
        args += ["--input", "-"]
    proc = subprocess.run(
        args,
        input=json.dumps(data) if data is not None else None,
        text=True,
        capture_output=True,
        timeout=25,
        check=True,
    )
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def load_module(filename, name):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def owner_probe(context):
    """Prove that the authenticated session owns the exact expected profile.

    A direct public profile route alone is insufficient. Success additionally
    requires an owner-only Edit profile control and no visible login gate.
    """
    page = await context.new_page()
    try:
        await page.goto(
            f"https://www.kwai.com/@{EXPECTED}",
            wait_until="domcontentloaded",
            timeout=15000,
        )
        await page.wait_for_timeout(1600)
        current = urlsplit(page.url)
        exact_route = (
            current.scheme == "https"
            and current.hostname == "www.kwai.com"
            and current.path.rstrip("/").lower() == f"/@{EXPECTED}"
        )
        flags = await page.evaluate(r"""() => {
          const visible = el => {
            const r = el.getBoundingClientRect(), s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const nodes = [...document.querySelectorAll('button,a,[role="button"],[role="menuitem"],span')]
            .filter(visible);
          const labels = nodes.map(el => ((el.innerText || el.textContent || '') + ' ' +
            (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '')).trim())
            .filter(t => t.length <= 80);
          return {
            owner_edit: labels.some(t => /^(edit profile|editar perfil)$/i.test(t)),
            login_gate: labels.some(t => /^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(t)) ||
              [...document.querySelectorAll('input')].some(el => visible(el) &&
                ['tel','email','password'].includes((el.getAttribute('type') || '').toLowerCase()))
          };
        }""")
        owner_edit = bool(flags.get("owner_edit"))
        login_gate = bool(flags.get("login_gate"))
        return {
            "chrome_connected": True,
            "expected_profile_route": bool(exact_route),
            "owner_edit_visible": owner_edit,
            "login_gate_visible": login_gate,
            "identity_verified": bool(exact_route and owner_edit and not login_gate),
            "probe_tab_temporary": True,
            "session_exported": False,
        }
    except Exception:
        return {
            "chrome_connected": True,
            "expected_profile_route": False,
            "owner_edit_visible": False,
            "login_gate_visible": False,
            "identity_verified": False,
            "probe_tab_temporary": True,
            "probe_failed": True,
            "session_exported": False,
        }
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def browser_action(action):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=7000)
        try:
            if not browser.contexts:
                return {"chrome_connected": True, "context_present": False}
            context = browser.contexts[0]
            if action == "inspect":
                return {
                    "chrome_connected": True,
                    "kwai_tab_present": any(
                        urlsplit(tab.url).hostname in ("kwai.com", "www.kwai.com", "studio.kwai.com")
                        for tab in context.pages
                    ),
                }
            if action == "profile_check":
                guard = load_module("kwai-identity-guard.py", "kwai_identity_guard_v2")
                evidence = await guard.inspect_browser()
                flags = evidence.get("evidence") or {}
                return {
                    "chrome_connected": bool(evidence.get("chrome_connected")),
                    "authenticated_ui_detected": bool(evidence.get("authenticated_ui_detected")),
                    "identity_verified": bool(evidence.get("identity_verified")),
                    "logout_visible": bool(flags.get("account_menu_logout_visible")),
                    "owner_edit_control_visible": bool(flags.get("profile_owner_control_visible")),
                    "session_exported": False,
                }
            if action == "owner_probe":
                helper = load_module("kwai-existing-tab-owner.py", "kwai_existing_tab_owner_v2")
                return await helper.inspect_existing_tab(context)
            if action == "create_probe":
                probe = load_module("kwai-create-surface-probe.py", "kwai_create_surface_probe_v2")
                return {"chrome_connected": True, **(await probe.inspect_existing_pages(context))}
            if action == "mobile_cdp_probe":
                probe = load_module("kwai-mobile-cdp-probe.py", "kwai_mobile_cdp_probe_v2")
                return {"chrome_connected": True, **(await probe.probe_mobile_client(context))}
            return {"chrome_connected": True, "unsupported_action": True}
        finally:
            await browser.close()


def main():
    STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    seen = set(json.loads(STATE.read_text())) if STATE.exists() else set()
    print("KWAI_BRIDGE_V2_READY=latest_comments;no_session_export", flush=True)
    while True:
        try:
            # GitHub issue comments are chronological even when sort=desc is sent.
            # Explicitly traverse pages; otherwise new commands past 100 vanish.
            comments = []
            for page_number in range(1, 21):
                batch = gh(
                    "GET",
                    f"repos/{REPO}/issues/{ISSUE}/comments?per_page=100&page={page_number}",
                )
                comments.extend(batch)
                if len(batch) < 100:
                    break
            # Newest first so an old refresh command cannot starve new probes.
            for comment in reversed(comments):
                cid = str(comment["id"])
                if cid in seen:
                    continue
                seen.add(cid)
                STATE.write_text(json.dumps(sorted(seen)[-800:]))
                STATE.chmod(0o600)
                if (comment.get("user") or {}).get("login", "").lower() != OWNER:
                    continue
                match = COMMAND.fullmatch((comment.get("body") or "").strip())
                if not match:
                    continue
                action, nonce = match.groups()
                if action == "refresh_bridge":
                    checkout = Path(__file__).resolve().parent.parent
                    pull = subprocess.run(
                        ["git", "pull", "--ff-only", "origin", "main"],
                        cwd=checkout,
                        capture_output=True,
                        text=True,
                        timeout=35,
                    )
                    outcome = {
                        "nonce": nonce,
                        "status": "ok" if pull.returncode == 0 else "error",
                        "refresh_started": pull.returncode == 0,
                        "chrome_profile_untouched": True,
                        "bridge_version": 2,
                    }
                else:
                    try:
                        result = asyncio.run(browser_action(action))
                        outcome = {"nonce": nonce, "status": "ok", "bridge_version": 2, **result}
                    except Exception:
                        outcome = {
                            "nonce": nonce,
                            "status": "error",
                            "bridge_version": 2,
                            "reason": "chrome_unavailable_or_probe_failed",
                        }
                gh("POST", f"repos/{REPO}/issues/{ISSUE}/comments", {"body": "KWAI_BRIDGE_RESULT " + json.dumps(outcome, sort_keys=True)})
                if action == "refresh_bridge" and outcome["status"] == "ok":
                    log = STATE.parent / "bridge-v2-refresh.log"
                    with log.open("ab") as stream:
                        subprocess.Popen(
                            ["bash", ".devcontainer/kwai-start.sh"],
                            cwd=checkout,
                            stdin=subprocess.DEVNULL,
                            stdout=stream,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    return
        except Exception:
            print("KWAI_BRIDGE_V2_POLL_RETRY", flush=True)
        time.sleep(6)


if __name__ == "__main__":
    main()
