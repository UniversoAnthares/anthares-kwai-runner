"""Device authentication bootstrap for a secondary ARA control plane.

A valid token is learned once from the canonical Cloudflare control's auth-check
endpoint and stored only as a SHA-256 hash in shared PostgreSQL state. Afterwards
the secondary control validates the device independently of the canonical service.
"""
import hashlib
import os
import secrets

import requests
from flask import request

from ara_state_store import build_store

_PRIMARY_AUTH_CHECK = os.getenv(
    "ARA_PRIMARY_AUTH_CHECK",
    "https://anthares-ara-backup.anthares1.workers.dev/v1/device/auth-check",
)
_STORE = build_store()


def _valid_device(device):
    return bool(device) and all(
        c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        for c in device
    )


def _valid_hash(value):
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _env_name(device):
    return "ARA_DEVICE_HASH_" + "".join(c if c.isalnum() else "_" for c in device.upper())


def _stored_hash(device):
    try:
        with _STORE._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS ara_device_auth(
                     device_id TEXT PRIMARY KEY,
                     token_hash TEXT NOT NULL,
                     updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                   )"""
            )
            cur.execute("SELECT token_hash FROM ara_device_auth WHERE device_id=%s", (device,))
            row = cur.fetchone()
            conn.commit()
            if not row:
                return ""
            value = row[0] if not isinstance(row, dict) else row.get("token_hash", "")
            value = str(value or "").strip().lower()
            return value if _valid_hash(value) else ""
    except Exception:
        return ""


def _remember(device, token_hash):
    if not _valid_hash(token_hash):
        return False
    try:
        with _STORE._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS ara_device_auth(
                     device_id TEXT PRIMARY KEY,
                     token_hash TEXT NOT NULL,
                     updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                   )"""
            )
            cur.execute(
                """INSERT INTO ara_device_auth(device_id,token_hash,updated_at)
                   VALUES(%s,%s,now())
                   ON CONFLICT(device_id) DO UPDATE
                   SET token_hash=excluded.token_hash, updated_at=now()""",
                (device, token_hash),
            )
            conn.commit()
        return True
    except Exception:
        return False


def register(app):
    @app.before_request
    def ara_secondary_device_auth_bootstrap():
        if not request.path.startswith("/v1/device/"):
            return None
        device = request.headers.get("X-Anthares-Device", "").strip()
        header = request.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        if not _valid_device(device) or not token:
            return None

        actual = hashlib.sha256(token.encode("utf-8")).hexdigest()
        env_name = _env_name(device)
        env_hash = os.getenv(env_name, "").strip().lower()
        if _valid_hash(env_hash) and secrets.compare_digest(actual, env_hash):
            _remember(device, actual)
            return None

        durable = _stored_hash(device)
        if durable and secrets.compare_digest(actual, durable):
            os.environ[env_name] = actual
            return None

        try:
            response = requests.get(
                _PRIMARY_AUTH_CHECK,
                headers={"Authorization": header, "X-Anthares-Device": device},
                timeout=6,
                allow_redirects=False,
            )
        except requests.RequestException:
            return None
        if response.status_code != 200:
            return None

        if _remember(device, actual):
            os.environ[env_name] = actual
        return None
