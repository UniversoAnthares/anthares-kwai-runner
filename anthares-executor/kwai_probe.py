"""Read-only Kwai verification over loopback CDP.

Navigation is allowlisted to the expected profile and studio. The probe never
reads/returns cookies, localStorage, tokens, page text or account secrets, and
never clicks upload/publish controls.
"""
import json
import os
import time
import urllib.request
from urllib.parse import quote
import websocket

CDP = os.environ.get("CDP_HTTP", "http://127.0.0.1:9222").rstrip("/")
EXPECTED = os.environ.get("KWAI_EXPECTED_ACCOUNT", "lucasrosalem").lstrip("@").lower()


def targets():
    with urllib.request.urlopen(CDP + "/json/list", timeout=2) as response:
        return json.loads(response.read().decode())


def page_target():
    for target in targets():
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return target
    raise RuntimeError("no_page_target")


def call(ws, method, params=None, timeout=6):
    rid = int(time.time_ns() % 2_000_000_000)
    ws.send(json.dumps({"id": rid, "method": method, "params": params or {}}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ws.settimeout(max(.2, deadline - time.monotonic()))
        msg = json.loads(ws.recv())
        if msg.get("id") != rid:
            continue
        if "error" in msg:
            raise RuntimeError("cdp_error:" + method)
        return msg.get("result", {})
    raise RuntimeError("cdp_timeout:" + method)


def evaluate(ws, expression):
    result = call(ws, "Runtime.evaluate", {"expression": expression, "returnByValue": True, "userGesture": False})
    if result.get("exceptionDetails"):
        raise RuntimeError("javascript_exception")
    return result.get("result", {}).get("value")


def navigate(ws, url, expected_host, expected_path=None, timeout=18):
    if expected_host not in {"www.kwai.com", "studio.kwai.com"}:
        raise RuntimeError("host_not_allowlisted")
    call(ws, "Page.navigate", {"url": url})
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = evaluate(ws, "({host:location.hostname.toLowerCase(),path:location.pathname.replace(/\\/$/,'').toLowerCase(),ready:document.readyState})")
        if isinstance(state, dict) and state.get("host") == expected_host and state.get("ready") in {"interactive", "complete"}:
            if expected_path is None or state.get("path") == expected_path:
                time.sleep(1.2)
                return
        time.sleep(.35)
    raise RuntimeError("expected_surface_not_loaded")


PROFILE_JS = r'''(() => {
 const visible=e=>{if(!e)return false;const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0};
 const label=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute?.('aria-label')||'')+' '+(e.getAttribute?.('title')||'')).replace(/\s+/g,' ').trim();
 const nodes=[...document.querySelectorAll('a,button,[role="button"],[role="link"],[role="menuitem"],input,span,div')];
 const login=nodes.some(e=>visible(e)&&(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(label(e))||['email','tel','password'].includes((e.getAttribute?.('type')||'').toLowerCase())));
 const owner=nodes.some(e=>visible(e)&&(/^(edit profile|editar perfil)$/i.test(label(e))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(e.getAttribute?.('data-testid')||'')||/\/(profile|account)\/(edit|settings)(\/|$)/i.test(e.getAttribute?.('href')||'')));
 return {host:location.hostname.toLowerCase(),path:location.pathname.replace(/\/$/,'').toLowerCase(),login_gate:login,owner_edit:owner};
})()'''

STUDIO_JS = r'''(() => {
 const visible=e=>{if(!e)return false;const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0};
 const label=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute?.('aria-label')||'')+' '+(e.getAttribute?.('title')||'')).replace(/\s+/g,' ').trim();
 const nodes=[...document.querySelectorAll('a,button,label,[role="button"],[role="menuitem"],input')];
 const login=nodes.some(e=>visible(e)&&(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(label(e))||['email','tel','password'].includes((e.getAttribute?.('type')||'').toLowerCase())));
 const file=[...document.querySelectorAll('input[type="file"]')].some(e=>!e.disabled);
 const create=nodes.some(e=>visible(e)&&/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(label(e)));
 const publish=nodes.some(e=>visible(e)&&/^(publish|post|publicar|share|compartilhar)$/i.test(label(e)));
 return {host:location.hostname.toLowerCase(),login_gate:login,file_input:file,create_or_upload:create,publish_control:publish};
})()'''


def probe():
    if not EXPECTED or len(EXPECTED) > 64 or not all(c.isalnum() or c in "._-" for c in EXPECTED):
        raise RuntimeError("invalid_expected_account")
    target = page_target()
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=4, suppress_origin=True, http_no_proxy=["127.0.0.1", "localhost", "::1"])
    try:
        path = "/@" + EXPECTED
        navigate(ws, "https://www.kwai.com/" + quote("@" + EXPECTED, safe="@._-"), "www.kwai.com", path)
        profile = evaluate(ws, PROFILE_JS) or {}
        identity = bool(profile.get("host") == "www.kwai.com" and profile.get("path") == path and profile.get("owner_edit") and not profile.get("login_gate"))
        evidence = {"profile_path_ok": profile.get("path") == path, "owner_edit": bool(profile.get("owner_edit")), "profile_login_gate": bool(profile.get("login_gate"))}
        if not identity:
            return {"ok": True, "identity_verified": False, "upload_surface_verified": False, "session_state": "unauthenticated" if profile.get("login_gate") else "unknown", "evidence": evidence, "read_only": True}
        navigate(ws, "https://studio.kwai.com/", "studio.kwai.com")
        studio = evaluate(ws, STUDIO_JS) or {}
        upload = bool(studio.get("host") == "studio.kwai.com" and not studio.get("login_gate") and (studio.get("file_input") or studio.get("create_or_upload")))
        evidence["studio_host_ok"] = studio.get("host") == "studio.kwai.com"
        evidence["studio_login_gate"] = bool(studio.get("login_gate"))
        evidence["file_input"] = bool(studio.get("file_input"))
        evidence["create_or_upload"] = bool(studio.get("create_or_upload"))
        evidence["publish_control_visible"] = bool(studio.get("publish_control"))
        return {"ok": True, "identity_verified": True, "upload_surface_verified": upload, "session_state": "authenticated_surface" if upload else "authenticated_profile_only", "evidence": evidence, "read_only": True}
    finally:
        ws.close()
