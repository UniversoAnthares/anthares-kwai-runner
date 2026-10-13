import base64
import json
import secrets
import time
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import base_app
import migration_capsule

router = APIRouter()
ISSUER = "https://token.actions.githubusercontent.com"
JWKS_URL = ISSUER + "/.well-known/jwks"
AUDIENCE = "anthares-session-migration"
REPOSITORY = "UniversoAnthares/anthares-kwai-runner"
ALLOWED = {
    "refs/heads/feature/anthares-executor-failover": {
        REPOSITORY + "/.github/workflows/anthares-executor-qa.yml@refs/heads/feature/anthares-executor-failover",
        REPOSITORY + "/.github/workflows/anthares-executor-restored-qa.yml@refs/heads/feature/anthares-executor-failover",
    },
    "refs/heads/feature/anthares-reserva-ci": {
        REPOSITORY + "/.github/workflows/anthares-cloud-executor.yml@refs/heads/feature/anthares-reserva-ci",
    },
}
AAD = b"anthares-github-oidc-session-handoff-v1"
_JWKS = {"expires": 0.0, "keys": []}


class Request(BaseModel):
    id_token: str = Field(min_length=100, max_length=12000)
    public_key_pem: str = Field(min_length=300, max_length=8192)


def _b64url(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _keys():
    now = time.time()
    if _JWKS["expires"] > now and _JWKS["keys"]:
        return _JWKS["keys"]
    req = urllib.request.Request(JWKS_URL, headers={"Accept": "application/json", "User-Agent": "anthares-session-handoff/4"})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
    except Exception as exc:
        raise HTTPException(503, "github_oidc_jwks_unavailable") from exc
    keys = data.get("keys") if isinstance(data, dict) else None
    if not isinstance(keys, list) or not keys:
        raise HTTPException(503, "github_oidc_jwks_invalid")
    _JWKS.update({"expires": now + 300, "keys": keys})
    return keys


def _claims(token):
    try:
        head_raw, body_raw, sig_raw = token.split(".")
        header = json.loads(_b64url(head_raw))
        claims = json.loads(_b64url(body_raw))
        signature = _b64url(sig_raw)
    except Exception as exc:
        raise HTTPException(401, "invalid_github_oidc_token") from exc
    if header.get("alg") != "RS256" or not header.get("kid"):
        raise HTTPException(401, "invalid_github_oidc_header")
    jwk = next((x for x in _keys() if x.get("kid") == header["kid"] and x.get("kty") == "RSA"), None)
    if jwk is None:
        _JWKS["expires"] = 0
        jwk = next((x for x in _keys() if x.get("kid") == header["kid"] and x.get("kty") == "RSA"), None)
    if jwk is None:
        raise HTTPException(401, "github_oidc_signing_key_not_found")
    try:
        key = rsa.RSAPublicNumbers(int.from_bytes(_b64url(jwk["e"]), "big"), int.from_bytes(_b64url(jwk["n"]), "big")).public_key()
        key.verify(signature, (head_raw + "." + body_raw).encode(), padding.PKCS1v15(), hashes.SHA256())
    except Exception as exc:
        raise HTTPException(401, "github_oidc_signature_invalid") from exc
    aud = claims.get("aud")
    audiences = aud if isinstance(aud, list) else [aud]
    ref, workflow_ref = claims.get("ref"), claims.get("workflow_ref")
    if claims.get("iss") != ISSUER or claims.get("repository") != REPOSITORY or AUDIENCE not in audiences:
        raise HTTPException(403, "github_oidc_claims_rejected")
    if ref not in ALLOWED or workflow_ref not in ALLOWED[ref]:
        raise HTTPException(403, "github_oidc_workflow_rejected")
    if claims.get("event_name") not in {"push", "workflow_dispatch"}:
        raise HTTPException(403, "github_oidc_event_rejected")
    try:
        now = int(time.time())
        exp, iat = int(claims["exp"]), int(claims["iat"])
        nbf = int(claims.get("nbf", iat))
    except Exception as exc:
        raise HTTPException(401, "github_oidc_time_claims_invalid") from exc
    if exp <= now or nbf > now + 30 or iat > now + 30 or now - iat > 600 or exp - iat > 900:
        raise HTTPException(401, "github_oidc_token_expired_or_stale")
    return claims


def _collect():
    with base_app._BROWSER_LOCK:
        base_app._cdp_call("Network.enable", timeout=5.0)
        base_app._cdp_call("Network.setBlockedURLs", {"urls": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.avif", "*.mp4", "*.webm", "*.mov", "*.m3u8", "*.mp3", "*.woff", "*.woff2", "*.ttf"]}, timeout=5.0)
        try:
            base_app._cdp_call("Page.navigate", {"url": "https://www.kwai.com/@lucasrosalem"}, timeout=8.0)
            time.sleep(2.5)
            evidence = migration_capsule._evaluate_value("""(() => { const nodes=[...document.querySelectorAll('a,button,input,[role=button],[role=menuitem],span,div')]; const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}; const txt=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute?.('aria-label')||'')).replace(/\\s+/g,' ').trim(); const login=nodes.some(e=>vis(e)&&(/^(log\\s*in|login|sign\\s*in|entrar|fazer login)$/i.test(txt(e))||['password','tel'].includes((e.getAttribute?.('type')||'').toLowerCase()))); const owner=nodes.some(e=>vis(e)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(txt(e))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(e.getAttribute?.('data-testid')||'')||/\\/(profile|account)\\/(edit|settings)(\\/|$)/i.test(e.getAttribute?.('href')||''))); const logout=nodes.some(e=>vis(e)&&/^(log\\s*out|logout|sign\\s*out|sair)$/i.test(txt(e))); return {host_ok:location.hostname==='www.kwai.com',path_ok:location.pathname.replace(/\\/$/,'').toLowerCase()==='/@lucasrosalem',login_gate:login,owner_edit:owner,logout_visible:logout}; })()""")
            profile_ok = isinstance(evidence, dict) and evidence.get("host_ok") and evidence.get("path_ok") and not evidence.get("login_gate")
            strong_profile_marker = bool(profile_ok and (evidence.get("owner_edit") or evidence.get("logout_visible")))
            studio_evidence = {}
            if profile_ok and not strong_profile_marker:
                base_app._cdp_call("Page.navigate", {"url": "https://studio.kwai.com/"}, timeout=8.0)
                time.sleep(2.5)
                studio_evidence = migration_capsule._evaluate_value("""(() => { const body=(document.body?.innerText||'').slice(0,24000); const login=!!document.querySelector('input[type=password],input[type=tel],input[type=email]')||/(^|\\n)\\s*(log\\s*in|login|sign\\s*in|entrar|fazer login)\\s*($|\\n)/i.test(body); const file=!!document.querySelector('input[type=file]:not([disabled])'); const upload=/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(body); return {host_ok:location.hostname==='studio.kwai.com',login_gate:login,file_input:file,upload_control:upload}; })()""") or {}
            authenticated = bool(strong_profile_marker or (profile_ok and isinstance(studio_evidence, dict) and studio_evidence.get("host_ok") and not studio_evidence.get("login_gate") and (studio_evidence.get("file_input") or studio_evidence.get("upload_control"))))
            if not authenticated:
                raise HTTPException(409, {"error": "source_session_not_authenticated", "evidence": evidence if isinstance(evidence, dict) else {}, "studio": studio_evidence if isinstance(studio_evidence, dict) else {}})
            base_app._cdp_call("Page.navigate", {"url": "https://www.kwai.com/@lucasrosalem"}, timeout=8.0)
            time.sleep(1.5)
            cookies_result = base_app._cdp_call("Network.getAllCookies", timeout=8.0)
            storage_raw = migration_capsule._evaluate_value("JSON.stringify(Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>{const k=localStorage.key(i);return [k,localStorage.getItem(k)]})))")
        finally:
            try:
                base_app._cdp_call("Page.navigate", {"url": "about:blank"}, timeout=5.0)
                base_app._cdp_call("Network.setBlockedURLs", {"urls": []}, timeout=3.0)
            except Exception:
                pass
    cookies = [migration_capsule._cookie_projection(c) for c in cookies_result.get("cookies", []) if migration_capsule._is_kwai_domain(str(c.get("domain", "")))]
    if not cookies or len(cookies) > 128:
        raise HTTPException(409, "source_kwai_cookie_state_invalid")
    try:
        storage = json.loads(storage_raw or "{}")
    except Exception:
        storage = {}
    if not isinstance(storage, dict) or len(storage) > 256:
        raise HTTPException(413, "kwai_local_storage_too_large")
    storage = {str(k): str(v) for k, v in storage.items() if len(str(k)) <= 512 and len(str(v)) <= 32768}
    return cookies, storage


@router.post("/migration/github-oidc-capsule")
def handoff(req: Request):
    claims = _claims(req.id_token)
    try:
        recipient = serialization.load_pem_public_key(req.public_key_pem.encode())
    except Exception as exc:
        raise HTTPException(422, "recipient_public_key_invalid") from exc
    if not isinstance(recipient, rsa.RSAPublicKey) or recipient.key_size < 3072:
        raise HTTPException(422, "recipient_public_key_too_weak")
    cookies, storage = _collect()
    plaintext = json.dumps({"version": 3, "created_at": int(time.time()), "repository": claims.get("repository"), "cookies": cookies, "local_storage": storage}, separators=(",", ":"), ensure_ascii=False).encode()
    if len(plaintext) > 512 * 1024:
        raise HTTPException(413, "kwai_state_too_large")
    key, nonce = secrets.token_bytes(32), secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, AAD)
    wrapped = recipient.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    return JSONResponse({"version": 3, "alg": "RSA-OAEP-256+A256GCM", "aad": base64.b64encode(AAD).decode(), "wrapped_key": base64.b64encode(wrapped).decode(), "nonce": base64.b64encode(nonce).decode(), "ciphertext": base64.b64encode(ciphertext).decode(), "cookie_count": len(cookies), "local_storage_count": len(storage), "source_identity_verified": True}, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})
