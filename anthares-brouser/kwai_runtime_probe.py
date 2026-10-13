#!/usr/bin/env python3
"""Fast, fail-closed verification of the restored Kwai browser profile.

No cookies, tokens or storage are exported. Heavy assets are blocked, each
navigation is bounded independently, and the tab always returns to about:blank
so a verification attempt cannot leave the 512 MiB Render service on a heavy
Kwai page.
"""
import json
import os
import time
import urllib.request

import websocket

CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))
CDP_HTTP = f"http://127.0.0.1:{CDP_PORT}"
EXPECTED = os.environ.get("KWAI_EXPECTED_ACCOUNT", "lucasrosalem").lstrip("@").lower()
PROFILE_URL = f"https://www.kwai.com/@{EXPECTED}"
STUDIO_URL = "https://studio.kwai.com/"
NAV_SECONDS = float(os.environ.get("KWAI_PROBE_NAV_SECONDS", "5"))

BLOCKED = [
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.avif", "*.ico",
    "*.mp4", "*.webm", "*.mov", "*.m3u8", "*.ts", "*.mp3", "*.aac",
    "*.woff", "*.woff2", "*.ttf", "*.otf",
    "*doubleclick*", "*google-analytics*", "*googletagmanager*",
]


def targets():
    with urllib.request.urlopen(f"{CDP_HTTP}/json/list", timeout=2) as response:
        return json.loads(response.read().decode("utf-8"))


def page_target():
    for target in targets():
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return target
    raise RuntimeError("no_page_target")


def cdp(ws, method, params=None, timeout=4):
    rid = int(time.time_ns() % 2_000_000_000)
    ws.send(json.dumps({"id": rid, "method": method, "params": params or {}}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ws.settimeout(max(0.2, deadline - time.monotonic()))
        message = json.loads(ws.recv())
        if message.get("id") != rid:
            continue
        if "error" in message:
            raise RuntimeError(f"cdp_error:{method}")
        return message.get("result", {})
    raise RuntimeError(f"cdp_timeout:{method}")


def evaluate(ws, expression, timeout=3):
    out = cdp(ws, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "userGesture": False,
    }, timeout=timeout)
    if out.get("exceptionDetails"):
        raise RuntimeError("javascript_exception")
    return out.get("result", {}).get("value")


def navigate(ws, url, seconds=NAV_SECONDS):
    cdp(ws, "Page.navigate", {"url": url}, timeout=3)
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        time.sleep(0.35)
        try:
            ready = evaluate(ws, "document.readyState", timeout=1.2)
            if ready in ("interactive", "complete"):
                break
        except Exception:
            pass
    try:
        cdp(ws, "Page.stopLoading", timeout=1.5)
    except Exception:
        pass
    time.sleep(0.25)


def blank(ws):
    try:
        cdp(ws, "Page.navigate", {"url": "about:blank"}, timeout=2)
        time.sleep(0.25)
        cdp(ws, "Page.stopLoading", timeout=1)
    except Exception:
        pass
    for method in ("HeapProfiler.collectGarbage", "Memory.forciblyPurgeJavaScriptMemory"):
        try:
            cdp(ws, method, timeout=1)
        except Exception:
            pass


def profile_probe(ws):
    navigate(ws, PROFILE_URL)
    return evaluate(ws, r'''(() => {
      const expected = ''' + json.dumps(EXPECTED) + r''';
      const body = (document.body?.innerText || '').slice(0, 24000);
      const low = body.toLowerCase();
      const inputs = [...document.querySelectorAll('input')];
      const loginInput = inputs.some(el => ['email','tel','password'].includes((el.type||'').toLowerCase()));
      const loginText = /(^|\n)\s*(log\s*in|login|sign\s*in|entrar|fazer login)\s*($|\n)/i.test(body);
      const ownerEdit = /(^|\n)\s*(edit profile|editar perfil)\s*($|\n)/i.test(body) ||
        !!document.querySelector('[data-testid*="edit-profile" i],[href*="/profile/edit" i],[href*="/account/edit" i]');
      const exactHandle = low.includes('@' + expected) || low.split(/\s+/).includes(expected);
      return {
        host: location.hostname.toLowerCase(),
        path: location.pathname.replace(/\/$/,'').toLowerCase(),
        owner_edit: ownerEdit,
        exact_handle: exactHandle,
        login_gate: loginInput || loginText
      };
    })()''', timeout=3)


def studio_probe(ws):
    navigate(ws, STUDIO_URL)
    return evaluate(ws, r'''(() => {
      const body = (document.body?.innerText || '').slice(0, 24000);
      const inputs = [...document.querySelectorAll('input')];
      const loginInput = inputs.some(el => ['email','tel','password'].includes((el.type||'').toLowerCase()));
      const loginText = /(^|\n)\s*(log\s*in|login|sign\s*in|entrar|fazer login)\s*($|\n)/i.test(body);
      const fileInput = [...document.querySelectorAll('input[type="file"]')].some(el => !el.disabled);
      const createOrUpload = /upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(body);
      const publish = /(^|\n)\s*(publish|post|publicar|share|compartilhar)\s*($|\n)/i.test(body);
      return {
        host: location.hostname.toLowerCase(),
        login_gate: loginInput || loginText,
        file_input: fileInput,
        create_or_upload: createOrUpload,
        publish_control: publish
      };
    })()''', timeout=3)


def main():
    result = {
        "ok": False,
        "expected_account": EXPECTED,
        "identity_verified": False,
        "studio_upload_ready": False,
        "session_state": "unknown",
        "session_exported": False,
        "bounded_navigation": True,
        "media_blocked": True,
    }
    ws = None
    try:
        target = page_target()
        ws = websocket.create_connection(
            target["webSocketDebuggerUrl"], timeout=3, suppress_origin=True,
            http_no_proxy=["127.0.0.1", "localhost", "::1"],
        )
        cdp(ws, "Network.enable", timeout=2)
        cdp(ws, "Network.setBlockedURLs", {"urls": BLOCKED}, timeout=2)
        cdp(ws, "Page.enable", timeout=2)

        try:
            profile = profile_probe(ws)
        except Exception as exc:
            profile = {}
            result["profile_error"] = str(exc)[:80]
        if not isinstance(profile, dict):
            profile = {}
        identity = bool(
            profile.get("host") == "www.kwai.com"
            and profile.get("path") == "/@" + EXPECTED
            and profile.get("owner_edit")
            and not profile.get("login_gate")
        )
        result["profile"] = {
            "exact_route": profile.get("path") == "/@" + EXPECTED,
            "owner_edit": bool(profile.get("owner_edit")),
            "exact_handle": bool(profile.get("exact_handle")),
            "login_gate": bool(profile.get("login_gate")),
        }
        result["identity_verified"] = identity
        result["session_state"] = (
            "authenticated" if identity
            else "unauthenticated" if profile.get("login_gate")
            else "unknown"
        )

        blank(ws)

        try:
            studio = studio_probe(ws)
        except Exception as exc:
            studio = {}
            result["studio_error"] = str(exc)[:80]
        if not isinstance(studio, dict):
            studio = {}
        ready = bool(
            identity
            and studio.get("host") == "studio.kwai.com"
            and not studio.get("login_gate")
            and (studio.get("file_input") or studio.get("create_or_upload"))
        )
        result["studio"] = {
            "host_ok": studio.get("host") == "studio.kwai.com",
            "login_gate": bool(studio.get("login_gate")),
            "file_input": bool(studio.get("file_input")),
            "create_or_upload": bool(studio.get("create_or_upload")),
            "publish_control": bool(studio.get("publish_control")),
        }
        result["studio_upload_ready"] = ready
        result["ok"] = bool(identity and ready)
    except Exception as exc:
        result["error"] = str(exc)[:100]
    finally:
        if ws is not None:
            blank(ws)
            try:
                cdp(ws, "Network.setBlockedURLs", {"urls": []}, timeout=1)
            except Exception:
                pass
            try:
                ws.close()
            except Exception:
                pass
    print("ANTHARES_KWAI_RUNTIME_PROBE=" + json.dumps(result, separators=(",", ":")), flush=True)
    raise SystemExit(0 if result.get("ok") else 3)


if __name__ == "__main__":
    main()
