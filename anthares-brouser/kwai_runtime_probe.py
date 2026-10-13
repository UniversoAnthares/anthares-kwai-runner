#!/usr/bin/env python3
"""Fail-closed, read-only proof for an already-loaded Kwai surface.

The runtime itself chooses START_URL. This probe never navigates, uploads,
publishes, reads cookies/tokens/storage, or exports page text. It only returns
bounded boolean evidence from the currently loaded page.
"""
import json
import os
import time
import urllib.request

import websocket

CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))
CDP_HTTP = f"http://127.0.0.1:{CDP_PORT}"
EXPECTED = os.environ.get("KWAI_EXPECTED_ACCOUNT", "lucasrosalem").lstrip("@").lower()
MODE = os.environ.get("KWAI_PROBE_MODE", "profile").strip().lower()
WAIT_SECONDS = float(os.environ.get("KWAI_PROBE_WAIT_SECONDS", "12"))


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
    result = cdp(ws, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "userGesture": False,
    }, timeout=timeout)
    if result.get("exceptionDetails"):
        raise RuntimeError("javascript_exception")
    return result.get("result", {}).get("value")


def wait_for_host(ws, wanted):
    deadline = time.monotonic() + WAIT_SECONDS
    last = ""
    while time.monotonic() < deadline:
        try:
            state = evaluate(ws, "({host:location.hostname.toLowerCase(),ready:document.readyState})", timeout=2)
            if isinstance(state, dict):
                last = state.get("host", "")
                if last == wanted and state.get("ready") in ("interactive", "complete"):
                    return True
        except Exception:
            pass
        time.sleep(0.35)
    return last == wanted


PROFILE_JS = r'''(() => {
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
  return {
    host: location.hostname.toLowerCase(),
    exact_route: location.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected,
    owner_edit: ownerEdit,
    exact_handle: exactHandle,
    login_gate: loginGate
  };
})()'''

STUDIO_JS = r'''(() => {
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
  return {
    host: location.hostname.toLowerCase(),
    login_gate: loginGate,
    file_input: fileInput,
    create_or_upload: createOrUpload,
    publish_control: publish
  };
})()'''


def main():
    if MODE not in {"profile", "studio"}:
        print("ANTHARES_KWAI_RUNTIME_PROBE=" + json.dumps({"ok":False,"error":"invalid_mode"}, separators=(",", ":")), flush=True)
        raise SystemExit(3)

    result = {
        "ok": False,
        "mode": MODE,
        "expected_account": EXPECTED,
        "identity_verified": False,
        "studio_upload_ready": False,
        "session_state": "unknown",
        "session_exported": False,
        "read_only": True,
        "navigation_performed": False,
    }
    ws = None
    try:
        target = page_target()
        ws = websocket.create_connection(
            target["webSocketDebuggerUrl"], timeout=3, suppress_origin=True,
            http_no_proxy=["127.0.0.1", "localhost", "::1"],
        )
        wanted = "www.kwai.com" if MODE == "profile" else "studio.kwai.com"
        if not wait_for_host(ws, wanted):
            raise RuntimeError("expected_host_not_loaded")
        try:
            cdp(ws, "Page.stopLoading", timeout=2)
        except Exception:
            pass

        if MODE == "profile":
            evidence = evaluate(ws, PROFILE_JS, timeout=4)
            if not isinstance(evidence, dict):
                evidence = {}
            verified = bool(
                evidence.get("host") == "www.kwai.com"
                and evidence.get("exact_route")
                and evidence.get("owner_edit")
                and not evidence.get("login_gate")
            )
            result["profile"] = {
                "exact_route": bool(evidence.get("exact_route")),
                "owner_edit": bool(evidence.get("owner_edit")),
                "exact_handle": bool(evidence.get("exact_handle")),
                "login_gate": bool(evidence.get("login_gate")),
            }
            result["identity_verified"] = verified
            result["session_state"] = "authenticated" if verified else ("unauthenticated" if evidence.get("login_gate") else "unknown")
            result["ok"] = verified
        else:
            evidence = evaluate(ws, STUDIO_JS, timeout=4)
            if not isinstance(evidence, dict):
                evidence = {}
            ready = bool(
                evidence.get("host") == "studio.kwai.com"
                and not evidence.get("login_gate")
                and (evidence.get("file_input") or evidence.get("create_or_upload"))
            )
            result["studio"] = {
                "host_ok": evidence.get("host") == "studio.kwai.com",
                "login_gate": bool(evidence.get("login_gate")),
                "file_input": bool(evidence.get("file_input")),
                "create_or_upload": bool(evidence.get("create_or_upload")),
                "publish_control": bool(evidence.get("publish_control")),
            }
            result["studio_upload_ready"] = ready
            result["session_state"] = "authenticated_surface" if ready else ("unauthenticated" if evidence.get("login_gate") else "unknown")
            result["ok"] = ready
    except Exception as exc:
        result["error"] = str(exc)[:100]
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    print("ANTHARES_KWAI_RUNTIME_PROBE=" + json.dumps(result, separators=(",", ":")), flush=True)
    raise SystemExit(0 if result.get("ok") else 3)


if __name__ == "__main__":
    main()
