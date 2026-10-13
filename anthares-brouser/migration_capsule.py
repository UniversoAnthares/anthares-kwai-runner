import base64
import json
import secrets
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

import base_app

router = APIRouter()
AAD = b"anthares-reserva-kwai-auth-v1"
PUBLIC_KEY_DER_B64 = (
    "MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAiBOOPUTbCSD35fAUX9l2z/znj52QS+ZK7x8GNwRxBrYhwtfuUmqoRVVotq0zpFiPK0d79Avj+B7bGu3L6Gy/4pRskrivd4MEL5WH3zSj09s3jgUYeNF4XCh9t8T7f5TDvRyJbkZPeR/n745G7vfEj2Jp7NGyIvqBW/yxODs62tm5W6Mfm0J82cs34JnEa3PsC2K3ssvPcEMgwltoiT5TOyg7awPlb/sb7BEf7PyH2Up8KThZUxJx525ibuLgsoFei4pzX2rrMm974NOEQiX+M+BLFse7YRD57LBYKe6I/vhMIEfczJh5gABXKiYa/0k6MNQUC1Xevv8mJuP1b+SZJ4ugsGFb/hZN54CbpMebv08EBTPrSa8c3y0+/98v8bxT+JrhubvaD4F1icjfrMQSl2SZMBu1DKGcrUl9kPdYW7IHq+m9UM860jlRjMOLxrenTBHq2gzqkDbZXp29FPDmz05auuRgkE5NLj9d1vAOUZ2nk7gxh2d2VjrCQUhQLESlAgMBAAE="
)


def _is_kwai_domain(domain: str) -> bool:
    host = (domain or "").lstrip(".").lower()
    return host == "kwai.com" or host.endswith(".kwai.com")


def _cookie_projection(cookie: dict) -> dict:
    allowed = {"name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite", "priority", "sameParty", "sourceScheme", "sourcePort"}
    return {key: cookie[key] for key in allowed if key in cookie}


def _evaluate_value(expression: str):
    result = base_app._cdp_call("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True,
        "userGesture": False,
    }, timeout=8.0)
    if result.get("exceptionDetails"):
        raise HTTPException(status_code=422, detail="migration_javascript_exception")
    return result.get("result", {}).get("value")


@router.get("/migration/kwai-capsule")
def export_kwai_capsule():
    """One-way encrypted cookie + localStorage capsule for Anthares-Reserva."""
    with base_app._BROWSER_LOCK:
        base_app._cdp_call("Network.enable", timeout=5.0)
        base_app._cdp_call("Network.setBlockedURLs", {"urls": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.avif", "*.mp4", "*.webm", "*.mov", "*.m3u8", "*.mp3", "*.woff", "*.woff2", "*.ttf"]}, timeout=5.0)
        cookies_result = base_app._cdp_call("Network.getAllCookies", timeout=8.0)
        try:
            base_app._cdp_call("Page.navigate", {"url": "https://www.kwai.com/@lucasrosalem"}, timeout=8.0)
            time.sleep(2.5)
            local_storage = _evaluate_value("JSON.stringify(Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>{const k=localStorage.key(i);return [k,localStorage.getItem(k)]})))")
            evidence = _evaluate_value("""(() => { const body=(document.body?.innerText||'').slice(0,24000); const nodes=[...document.querySelectorAll('a,button,input,[role=button],[role=menuitem],span,div')]; const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}; const txt=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute?.('aria-label')||'')).replace(/\\s+/g,' ').trim(); const login=nodes.some(e=>vis(e)&&(/^(log\\s*in|login|sign\\s*in|entrar|fazer login)$/i.test(txt(e))||['password','tel'].includes((e.getAttribute?.('type')||'').toLowerCase()))); const owner=nodes.some(e=>vis(e)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(txt(e))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(e.getAttribute?.('data-testid')||'')||/\\/(profile|account)\\/(edit|settings)(\\/|$)/i.test(e.getAttribute?.('href')||''))); const logout=nodes.some(e=>vis(e)&&/^(log\\s*out|logout|sign\\s*out|sair)$/i.test(txt(e))); return {host_ok:location.hostname==='www.kwai.com',path_ok:location.pathname.replace(/\\/$/,'').toLowerCase()==='/@lucasrosalem',login_gate:login,owner_edit:owner,logout_visible:logout,body_present:body.length>0}; })()""")
        finally:
            try:
                base_app._cdp_call("Page.navigate", {"url": "about:blank"}, timeout=5.0)
                base_app._cdp_call("Network.setBlockedURLs", {"urls": []}, timeout=3.0)
            except Exception:
                pass

    cookies = [_cookie_projection(c) for c in cookies_result.get("cookies", []) if _is_kwai_domain(str(c.get("domain", "")))]
    if not cookies:
        raise HTTPException(status_code=409, detail="no_kwai_cookie_state")
    if len(cookies) > 128:
        raise HTTPException(status_code=413, detail="kwai_cookie_state_too_large")
    try:
        storage = json.loads(local_storage or "{}")
    except Exception:
        storage = {}
    if not isinstance(storage, dict) or len(storage) > 256:
        raise HTTPException(status_code=413, detail="kwai_local_storage_too_large")
    storage = {str(k): str(v) for k, v in storage.items() if len(str(k)) <= 512 and len(str(v)) <= 32768}

    plaintext = json.dumps({"version": 2, "created_at": int(time.time()), "cookies": cookies, "local_storage": storage}, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(plaintext) > 512 * 1024:
        raise HTTPException(status_code=413, detail="kwai_state_too_large")

    public_key = serialization.load_der_public_key(base64.b64decode(PUBLIC_KEY_DER_B64))
    aes_key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, AAD)
    wrapped_key = public_key.encrypt(aes_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    envelope = {
        "version": 2,
        "alg": "RSA-OAEP-256+A256GCM",
        "aad": base64.b64encode(AAD).decode("ascii"),
        "wrapped_key": base64.b64encode(wrapped_key).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "cookie_count": len(cookies),
        "local_storage_count": len(storage),
        "source_evidence": evidence if isinstance(evidence, dict) else {},
    }
    return JSONResponse(envelope, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})
