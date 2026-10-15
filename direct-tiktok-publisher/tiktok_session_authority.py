#!/usr/bin/env python3
"""Canonical TikTok session authority backed by the Anthares Browser runtime vault."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VAULT_URL = os.getenv(
    "ANTHARES_TIKTOK_SESSION_VAULT_URL",
    "https://anthares-x-vault.anthares1.workers.dev/browser-state/runtime",
).strip()
EXPECTED_USERNAME = "universo.anthares"
P256_ORDER = int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)
AAD = b"anthares-browser-runtime-state-v1"
SCHEMA = "anthares.encrypted-browser-state.v1"


class SessionAuthorityError(RuntimeError):
    pass


def _secret() -> str:
    value = os.getenv("ARA_SHARED", "").strip()
    if not value:
        raise SessionAuthorityError("canonical_session_secret_missing")
    return value


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _derive_signer():
    raw = hashlib.sha256(("browser-vault-sign:" + _secret()).encode()).digest()
    scalar = int.from_bytes(raw, "big") % (P256_ORDER - 1) + 1
    return ec.derive_private_key(scalar, ec.SECP256R1())


def _signature(body: bytes = b"") -> tuple[str, str]:
    ts = str(int(time.time() * 1000))
    digest = hashlib.sha256(body).hexdigest()
    der = _derive_signer().sign((ts + "." + digest).encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return ts, _b64(r.to_bytes(32, "big") + s.to_bytes(32, "big"))


def _normalize_state(state: dict) -> dict:
    if not isinstance(state, dict) or not isinstance(state.get("cookies"), list) or not state.get("cookies"):
        raise SessionAuthorityError("canonical_session_empty")
    origins = state.get("origins")
    if not isinstance(origins, list):
        origins = []
    return {"cookies": state["cookies"], "origins": origins}


def _encrypt(state: dict) -> str:
    normalized = _normalize_state(state)
    raw = json.dumps(normalized, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    key = hashlib.sha256(("browser-vault-enc:" + _secret()).encode()).digest()
    nonce = os.urandom(12)
    return _b64(nonce + AESGCM(key).encrypt(nonce, raw, AAD))


def _decrypt(ciphertext: str) -> dict:
    blob = _b64d(ciphertext)
    if len(blob) < 29:
        raise SessionAuthorityError("canonical_session_ciphertext_invalid")
    key = hashlib.sha256(("browser-vault-enc:" + _secret()).encode()).digest()
    try:
        raw = AESGCM(key).decrypt(blob[:12], blob[12:], AAD)
        state = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise SessionAuthorityError("canonical_session_decrypt_failed") from exc
    return _normalize_state(state)


def _headers(body: bytes = b"") -> dict[str, str]:
    ts, sig = _signature(body)
    return {
        "X-Anthares-Browser-Timestamp": ts,
        "X-Anthares-Browser-Signature": sig,
        "Accept": "application/json",
        "User-Agent": "AntharesTikTokSessionAuthority/2.0",
    }


def _assert_runtime_url() -> None:
    if not VAULT_URL.endswith("/browser-state/runtime"):
        raise SessionAuthorityError("canonical_session_authority_must_be_runtime")


def load_canonical_state() -> tuple[dict, dict]:
    _assert_runtime_url()
    try:
        response = requests.get(VAULT_URL, headers=_headers(), timeout=25)
    except requests.RequestException as exc:
        raise SessionAuthorityError("canonical_session_vault_transport_failed") from exc
    if response.status_code != 200:
        try:
            error = str((response.json() or {}).get("error") or "")
        except Exception:
            error = ""
        suffix = error if error in {"unauthorized", "persistent_state_unavailable", "vault_integrity_failed"} else str(response.status_code)
        raise SessionAuthorityError("canonical_session_vault_http_" + suffix)
    try:
        payload = response.json()
    except ValueError as exc:
        raise SessionAuthorityError("canonical_session_vault_invalid_json") from exc
    ciphertext = str(payload.get("ciphertext") or "")
    if not payload.get("ok") or not payload.get("available") or not ciphertext:
        raise SessionAuthorityError("canonical_session_vault_empty")
    expected_sha = str(payload.get("sha256") or "").strip().lower()
    actual_sha = hashlib.sha256(ciphertext.encode("ascii")).hexdigest()
    if expected_sha and expected_sha != actual_sha:
        raise SessionAuthorityError("canonical_session_checksum_mismatch")
    state = _decrypt(ciphertext)
    meta = {
        "authority": "runtime",
        "vault_url": VAULT_URL,
        "ciphertext_sha256": actual_sha,
        "cookie_count": len(state["cookies"]),
        "expected_username": EXPECTED_USERNAME,
        "updated_at": payload.get("updated_at"),
    }
    return state, meta


def persist_canonical_state(state: dict) -> dict:
    """Encrypt and atomically replace the sole canonical runtime browser state."""
    _assert_runtime_url()
    normalized = _normalize_state(state)
    ciphertext = _encrypt(normalized)
    envelope = {
        "schema": SCHEMA,
        "ciphertext": ciphertext,
        "sha256": hashlib.sha256(ciphertext.encode("ascii")).hexdigest(),
    }
    body = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    headers = _headers(body)
    headers["Content-Type"] = "application/json"
    try:
        response = requests.post(VAULT_URL, data=body, headers=headers, timeout=25)
    except requests.RequestException as exc:
        raise SessionAuthorityError("canonical_session_vault_persist_transport_failed") from exc
    if response.status_code not in {200, 201}:
        try:
            error = str((response.json() or {}).get("error") or "")
        except Exception:
            error = ""
        raise SessionAuthorityError("canonical_session_vault_persist_http_" + (error or str(response.status_code)))
    try:
        payload = response.json()
    except ValueError as exc:
        raise SessionAuthorityError("canonical_session_vault_persist_invalid_json") from exc
    if not payload.get("ok"):
        raise SessionAuthorityError("canonical_session_vault_persist_rejected")
    return {
        "authority": "runtime",
        "vault_url": VAULT_URL,
        "ciphertext_sha256": envelope["sha256"],
        "cookie_count": len(normalized["cookies"]),
        "updated_at": payload.get("updated_at"),
    }


def materialize(path: str | os.PathLike[str]) -> dict:
    state, meta = load_canonical_state()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass
    return meta


if __name__ == "__main__":
    output = os.getenv("TIKTOK_STORAGE_STATE_FILE", "").strip()
    state, meta = load_canonical_state()
    if output:
        Path(output).write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(meta, sort_keys=True))
