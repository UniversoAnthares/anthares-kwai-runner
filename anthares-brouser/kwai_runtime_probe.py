#!/usr/bin/env python3
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


def targets():
    with urllib.request.urlopen(f"{CDP_HTTP}/json/list", timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def page_target():
    for target in targets():
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return target
    raise RuntimeError("no_page_target")


def cdp(ws, method, params=None, timeout=10):
    rid = int(time.time_ns() % 2_000_000_000)
    ws.send(json.dumps({"id": rid, "method": method, "params": params or {}}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ws.settimeout(max(0.2, deadline - time.monotonic()))
        msg = json.loads(ws.recv())
        if msg.get("id") != rid:
            continue
        if "error" in msg:
            raise RuntimeError(f"cdp_error:{method}")
        return msg.get("result", {})
    raise RuntimeError(f"cdp_timeout:{method}")


def evaluate(ws, expression):
    out = cdp(ws, "Runtime.evaluate", {
        "expression": expression,
        "awaitPromise": True,
        "returnByValue": True,
        "userGesture": True,
    }, timeout=12)
    if out.get("exceptionDetails"):
        raise RuntimeError("javascript_exception")
    return out.get("result", {}).get("value")


def navigate(ws, url, settle=2.0):
    cdp(ws, "Page.navigate", {"url": url}, timeout=10)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            if evaluate(ws, "document.readyState") in ("interactive", "complete"):
                break
        except Exception:
            pass
        time.sleep(0.25)
    time.sleep(settle)


def main():
    result = {
        "ok": False,
        "expected_account": EXPECTED,
        "identity_verified": False,
        "studio_upload_ready": False,
        "session_state": "unknown",
        "session_exported": False,
    }
    target = page_target()
    ws = websocket.create_connection(
        target["webSocketDebuggerUrl"], timeout=5, suppress_origin=True,
        http_no_proxy=["127.0.0.1", "localhost", "::1"],
    )
    original = None
    try:
        original = evaluate(ws, "location.href")
        navigate(ws, PROFILE_URL, settle=2.5)
        profile = evaluate(ws, r'''(() => {
          const expected = ''' + json.dumps(EXPECTED) + r''';
          const visible = el => {
            if (!el) return false;
            const s=getComputedStyle(el), r=el.getBoundingClientRect();
            return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
          };
          const label = el => ((el.innerText||el.textContent||'')+' '+(el.getAttribute?.('aria-label')||'')+' '+(el.getAttribute?.('title')||'')).replace(/\s+/g,' ').trim();
          const nodes=[...document.querySelectorAll('a,button,[role="button"],[role="link"],[role="menuitem"],input,span,div')];
          const loginGate=nodes.some(el=>visible(el)&&(
            /^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(label(el)) ||
            ['email','tel','password'].includes((el.getAttribute?.('type')||'').toLowerCase())
          ));
          const path=location.pathname.replace(/\/$/,'').toLowerCase();
          const exactRoute=path==='/@'+expected;
          const ownerEdit=nodes.some(el=>visible(el)&&(
            /^(edit profile|editar perfil)$/i.test(label(el)) ||
            /edit[-_ ]?profile|profile[-_ ]?edit/i.test((el.getAttribute?.('data-testid')||'')) ||
            /\/(profile|account)\/(edit|settings)(\/|$)/i.test((el.getAttribute?.('href')||''))
          ));
          const exactHandle=nodes.some(el=>{
            if(!visible(el)) return false;
            const t=(el.innerText||el.textContent||'').trim().replace(/^@/,'').toLowerCase();
            return t===expected;
          });
          return {host:location.hostname.toLowerCase(), exact_route:exactRoute, owner_edit:ownerEdit, exact_handle:exactHandle, login_gate:loginGate};
        })()''')
        if not isinstance(profile, dict):
            profile = {}
        identity = bool(
            profile.get("host") == "www.kwai.com"
            and profile.get("exact_route")
            and profile.get("owner_edit")
            and not profile.get("login_gate")
        )
        result["profile"] = {
            "exact_route": bool(profile.get("exact_route")),
            "owner_edit": bool(profile.get("owner_edit")),
            "exact_handle": bool(profile.get("exact_handle")),
            "login_gate": bool(profile.get("login_gate")),
        }
        result["identity_verified"] = identity
        result["session_state"] = "authenticated" if identity else ("unauthenticated" if profile.get("login_gate") else "unknown")

        navigate(ws, STUDIO_URL, settle=3.0)
        studio = evaluate(ws, r'''(() => {
          const visible = el => {
            if (!el) return false;
            const s=getComputedStyle(el), r=el.getBoundingClientRect();
            return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
          };
          const nodes=[...document.querySelectorAll('a,button,label,[role="button"],[role="menuitem"],input')];
          const label=el=>((el.innerText||el.textContent||'')+' '+(el.getAttribute?.('aria-label')||'')+' '+(el.getAttribute?.('title')||'')).replace(/\s+/g,' ').trim();
          const loginGate=nodes.some(el=>visible(el)&&(
            /^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(label(el)) ||
            ['email','tel','password'].includes((el.getAttribute?.('type')||'').toLowerCase())
          ));
          const fileInput=[...document.querySelectorAll('input[type="file"]')].some(el=>!el.disabled);
          const createOrUpload=nodes.some(el=>visible(el)&&/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post|create|criar/i.test(label(el)));
          const publish=nodes.some(el=>visible(el)&&/^(publish|post|publicar|share|compartilhar)$/i.test(label(el)));
          return {host:location.hostname.toLowerCase(), login_gate:loginGate, file_input:fileInput, create_or_upload:createOrUpload, publish_control:publish};
        })()''')
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
        result["ok"] = identity and ready
    except Exception as exc:
        result["error"] = type(exc).__name__
        result["error_detail"] = str(exc)[:180]
    finally:
        try:
            if isinstance(original, str) and original.startswith(("http://", "https://")):
                navigate(ws, original, settle=0.5)
        except Exception:
            result["restore_original_failed"] = True
        try:
            ws.close()
        except Exception:
            pass
    print("ANTHARES_KWAI_RUNTIME_PROBE=" + json.dumps(result, separators=(",", ":")), flush=True)
    raise SystemExit(0 if result.get("ok") else 3)


if __name__ == "__main__":
    main()
