"""Decrypt an ephemeral GitHub-OIDC Kwai handoff and import it into local Chromium.

This helper runs only inside the executor container. It never prints decrypted
session material. The private key and encrypted capsule are ephemeral files
mounted read-only by the workflow and destroyed by the host cleanup step.
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import kwai_probe

EXPECTED_REPOSITORY = "UniversoAnthares/anthares-kwai-runner"
EXPECTED_AAD = b"anthares-github-oidc-session-handoff-v1"
MAX_AGE_SECONDS = 300


def fail(message):
    print(json.dumps({"ok": False, "error": message}, separators=(",", ":")))
    raise SystemExit(2)


def load_and_decrypt(capsule_path, key_path):
    try:
        envelope = json.loads(Path(capsule_path).read_text())
        private_key = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
    except Exception:
        fail("handoff_input_invalid")
    if envelope.get("version") != 3 or envelope.get("alg") != "RSA-OAEP-256+A256GCM":
        fail("handoff_envelope_invalid")
    try:
        aad = base64.b64decode(envelope["aad"], validate=True)
        wrapped = base64.b64decode(envelope["wrapped_key"], validate=True)
        nonce = base64.b64decode(envelope["nonce"], validate=True)
        ciphertext = base64.b64decode(envelope["ciphertext"], validate=True)
    except Exception:
        fail("handoff_encoding_invalid")
    if aad != EXPECTED_AAD or len(nonce) != 12 or len(ciphertext) > 600 * 1024:
        fail("handoff_bounds_invalid")
    try:
        aes_key = private_key.decrypt(
            wrapped,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        plaintext = AESGCM(aes_key).decrypt(nonce, ciphertext, aad)
        state = json.loads(plaintext)
    except Exception:
        fail("handoff_decryption_failed")
    if not isinstance(state, dict) or state.get("version") != 3 or state.get("repository") != EXPECTED_REPOSITORY:
        fail("handoff_state_invalid")
    try:
        created_at = int(state.get("created_at", 0))
    except Exception:
        fail("handoff_timestamp_invalid")
    now = int(time.time())
    if created_at <= 0 or created_at > now + 30 or now - created_at > MAX_AGE_SECONDS:
        fail("handoff_expired")
    return state


def main():
    if len(sys.argv) != 3:
        fail("usage_invalid")
    state = load_and_decrypt(sys.argv[1], sys.argv[2])
    try:
        result = kwai_probe.import_state(state)
    except Exception as exc:
        fail("session_import_" + type(exc).__name__)
    safe = {
        "ok": bool(result.get("ok")),
        "cookies_imported": int(result.get("cookies_imported", 0)),
        "local_storage_imported": int(result.get("local_storage_imported", 0)),
    }
    print(json.dumps(safe, separators=(",", ":")))
    if not safe["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
