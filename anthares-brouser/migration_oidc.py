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
ALLOWED_REFS = {
    "refs/heads/feature/anthares-executor-failover": {
        REPOSITORY + "/.github/workflows/anthares-executor-qa.yml@refs/heads/feature/anthares-executor-failover",
        REPOSITORY + "/.github/workflows/anthares-executor-restored-qa.yml@refs/heads/feature/anthares-executor-failover",
    },
    "refs/heads/feature/anthares-reserva-ci": {
        REPOSITORY + "/.github/workflows/anthares-cloud-executor.yml@refs/heads/feature/anthares-reserva-ci",
    },
}
AAD = b"anthares-github-oidc-session-handoff-v1"
_JWKS_CACHE = {"expires": 0.0, "keys": []}


class OidcCapsuleRequest(BaseModel):
    id_token: str = Field(min_length=100, max_length=12000)
    public_key_pem: str = Field(min_length=300, max_length=8192)


def _b64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _jwks():
    now = time.time()
    if _JWKS_CACHE["expires"] > now and _JWKS_CACHE["keys"]:
        return _JWKS_CACHE["keys"]
    req = urllib.request.Request(
        JWKS_URL,
        headers={"Accept": "application/json", "User-Agent": "anthares-session-handoff/1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="github_oidc_jwks_unavailable") from exc
    keys = data.get("keys") if isinstance(data, dict) else None
    if not isinstance(keys, list) or not keys:
        raise HTTPException(status_code=503, detail="github_oidc_jwks_invalid")
    _JWKS_CACHE.update({"expires": now + 300, "keys": keys})
    return keys


def _verify_oidc(token: str) -> dict:
    try:
        head_raw, payload_raw, sig_raw = token.split(".")
        header = json.loads(_b64url(head_raw))
        claims = json.loads(_b64url(payload_raw))
        signature = _b64url(sig_raw)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid_github_oidc_token") from exc
    if header.get("alg") != "RS256" or not header.get("kid"):
        raise HTTPException(status_code=401, detail="invalid_github_oidc_header")
    jwk = next(
        (k for k in _jwks() if k.get("kid") == header["kid"] and k.get("kty") == "RSA"),
        None,
    )
    if jwk is None:
        _JWKS_CACHE["expires"] = 0
        jwk = next(
            (k for k in _jwks() if k.get("kid") == header["kid"] and k.get("kty") == "RSA"),
            None,
        )
    if jwk is None:
        raise HTTPException(status_code=401, detail="github_oidc_signing_key_not_found")
    try:
        n = int.from_bytes(_b64url(jwk["n"]), "big")
        e = int.from_bytes(_b64url(jwk["e"]), "big")
        public_key = rsa.RSAPublicNumbers(e, n).public_key()
        public_key.verify(
            signature,
            (head_raw + "." + payload_raw).encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="github_oidc_signature_invalid") from exc

    now = int(time.time())
    aud = claims.get("aud")
    audiences = aud if isinstance(aud, list) else [aud]
    ref = claims.get("ref")
    workflow_ref = claims.get("workflow_ref")
    if claims.get("iss") != ISSUER or claims.get("repository") != REPOSITORY or AUDIENCE not in audiences:
        raise HTTPException(status_code=403, detail="github_oidc_claims_rejected")
    if ref not in ALLOWED_REFS:
        raise HTTPException(status_code=403, detail="github_oidc_ref_rejected")
    if workflow_ref not in ALLOWED_REFS[ref]:
        raise HTTPException(status_code=403, detail="github_oidc_workflow_rejected")
    if claims.get("sub") != f"repo:{REPOSITORY}:ref:{ref}":
        raise HTTPException(status_code=403, detail="github_oidc_subject_rejected")
    if claims.get("event_name") not in {"push", "workflow_dispatch"}:
        raise HTTPException(status_code=403, detail="github_oidc_event_rejected")
    try:
        exp, iat = int(claims["exp"]), int(claims["iat"])
        nbf = int(claims.get("nbf", iat))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="github_oidc_time_claims_invalid") from exc
    if exp <= now or nbf > now + 30 or iat > now + 30 or now - iat > 600 or exp - iat > 900:
        raise HTTPException(status_code=401, detail="github_oidc_token_expired_or_stale")
    return claims


def _collect_kwai_state() -> tuple[list[dict], dict, dict]:
    with base_app._BROWSER_LOCK:
        base_app._cdp_call("Network.enable", timeout=5.0)
        base_app._cdp_call(
            "Network.setBlockedURLs",
            {
                "urls": [
                    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.avif",
                    "*.mp4", "*.webm", "*.mov", "*.m3u8", "*.mp3", "*.woff",
                    "*.woff2", "*.ttf",
                ]
            },
            timeout=5.0,
        )
        try:
            base_app._cdp_call(
                "Page.navigate", {"url": "https://www.kwai.com/@lucasrosalem"}, timeout=8.0
            )
            time.sleep(2.5)
            evidence = migration_capsule._evaluate_value(
                """(() => { const body=(document.body?.innerText||'').slice(0,24000); const nodes=[...document.querySelectorAll('a,button,input,[role=button],[role=menuitem],span,div')]; const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}; const txt=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute?.('aria-label')||'')).replace(/\\s+/g,' ').trim(); const login=nodes.some(e=>vis(e)&&(/^(log\\s*in|login|sign\\s*in|entrar|fazer login)$/i.test(txt(e))||['password','tel'].includes((e.getAttribute?.('type')||'').toLowerCase()))); const owner=nodes.some(e=>vis(e)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(txt(e))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(e.getAttribute?.('data-testid')||'')||/\\/(profile|account)\\/(edit|settings)(\\/|$)/i.test(e.getAttribute?.('href')||''))); return {host_ok:location.hostname==='www.kwai.com',path_ok:location.pathname.replace(/\\/$/,'').toLowerCase()==='/@lucasrosalem',login_gate:login,owner_edit:owner,body_present:body.length>0}; })()"""
            )
            if (
                not isinstance(evidence, dict)
                or not evidence.get("host_ok")
                or not evidence.get("path_ok")
                or evidence.get("login_gate")
                or not evidence.get("owner_edit")
            ):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "source_session_not_authenticated",
                        "evidence": evidence if isinstance(evidence, dict) else {},
                    },
                )
            cookies_result = base_app._cdp_call("Network.getAllCookies", timeout=8.0)
            local_storage_raw = migration_capsule._evaluate_value(
                "JSON.stringify(Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>{const k=localStorage.key(i);return [k,localStorage.getItem(k)]})))"
            )
        finally:
            try:
                base_app._cdp_call("Page.navigate", {"url": "about:blank"}, timeout=5.0)
                base_app._cdp_call("Network.setBlockedURLs", {"urls": []}, timeout=3.0)
            except Exception:
                pass
    cookies = [
        migration_capsule._cookie_projection(c)
        for c in cookies_result.get("cookies", [])
        if migration_capsule._is_kwai_domain(str(c.get("domain", "")))
    ]
    if not cookies or len(cookies) > 128:
        raise HTTPException(status_code=409, detail="source_kwai_cookie_state_invalid")
    try:
        storage = json.loads(local_storage_raw or "{}")
    except Exception:
        storage = {}
    if not isinstance(storage, dict) or len(storage) > 256:
        raise HTTPException(status_code=413, detail="source_kwai_local_storage_too_large")
    storage = {
        str(k): str(v)
        for k, v in storage.items()
        if len(str(k)) <= 512 and len(str(v)) <= 32768
    }
    return cookies, storage, evidence


@router.post("/migration/github-oidc-capsule")
def github_oidc_capsule(req: OidcCapsuleRequest):
    claims = _verify_oidc(req.id_token)
    try:
        recipient = serialization.load_pem_public_key(req.public_key_pem.encode("ascii"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="recipient_public_key_invalid") from exc
    if not isinstance(recipient, rsa.RSAPublicKey) or recipient.key_size < 3072:
        raise HTTPException(status_code=422, detail="recipient_public_key_too_weak")
    cookies, storage, evidence = _collect_kwai_state()
    plaintext = json.dumps(
        {
            "version": 3,
            "created_at": int(time.time()),
            "repository": claims.get("repository"),
            "cookies": cookies,
            "local_storage": storage,
        },
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if len(plaintext) > 512 * 1024:
        raise HTTPException(status_code=413, detail="kwai_state_too_large")
    aes_key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, AAD)
    wrapped = recipient.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    envelope = {
        "version": 3,
        "alg": "RSA-OAEP-256+A256GCM",
        "aad": base64.b64encode(AAD).decode("ascii"),
        "wrapped_key": base64.b64encode(wrapped).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "cookie_count": len(cookies),
        "local_storage_count": len(storage),
        "source_identity_verified": True,
    }
    return JSONResponse(
        envelope,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )
