import base64
import json
import os
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
    allowed = {
        "name", "value", "domain", "path", "expires", "httpOnly", "secure",
        "sameSite", "priority", "sameParty", "sourceScheme", "sourcePort",
    }
    return {key: cookie[key] for key in allowed if key in cookie}


@router.get("/migration/kwai-capsule")
def export_kwai_capsule():
    """Export only an RSA/AES encrypted Kwai cookie capsule.

    The private half exists only in the Anthares-Reserva Cloudflare Worker.
    No plaintext cookie, token or state key is returned or logged here.
    This route is temporary and must be removed after migration validation.
    """
    with base_app._BROWSER_LOCK:
        base_app._cdp_call("Network.enable", timeout=5.0)
        result = base_app._cdp_call("Network.getAllCookies", timeout=8.0)

    cookies = [
        _cookie_projection(cookie)
        for cookie in result.get("cookies", [])
        if _is_kwai_domain(str(cookie.get("domain", "")))
    ]
    if not cookies:
        raise HTTPException(status_code=409, detail="no_kwai_cookie_state")
    if len(cookies) > 128:
        raise HTTPException(status_code=413, detail="kwai_cookie_state_too_large")

    plaintext = json.dumps(
        {"version": 1, "created_at": int(time.time()), "cookies": cookies},
        separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    if len(plaintext) > 128 * 1024:
        raise HTTPException(status_code=413, detail="kwai_cookie_state_too_large")

    public_key = serialization.load_der_public_key(base64.b64decode(PUBLIC_KEY_DER_B64))
    aes_key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, AAD)
    wrapped_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    envelope = {
        "version": 1,
        "alg": "RSA-OAEP-256+A256GCM",
        "aad": base64.b64encode(AAD).decode("ascii"),
        "wrapped_key": base64.b64encode(wrapped_key).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "cookie_count": len(cookies),
    }
    return JSONResponse(envelope, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})
