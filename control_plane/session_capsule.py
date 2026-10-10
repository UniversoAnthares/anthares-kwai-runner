"""Private browser-session capsule for cloud runners.

The capsule is supplied only through a secret environment variable. This module never
prints, persists in the repository, or uploads its contents as an artifact.
"""
import base64
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_DOMAINS = {"tiktok.com", "kwai.com"}


def decode_capsule(value):
    if not value:
        raise RuntimeError("session_capsule_missing")
    try:
        raw = base64.b64decode(value, validate=True)
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("session_capsule_invalid") from exc
    domain = data.get("domain")
    if domain not in ALLOWED_DOMAINS:
        raise RuntimeError("session_capsule_domain_not_allowed")
    expires_at = data.get("expires_at")
    if not expires_at:
        raise RuntimeError("session_capsule_expiry_missing")
    expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expiry <= datetime.now(timezone.utc):
        raise RuntimeError("session_capsule_expired")
    state = data.get("storage_state")
    if not isinstance(state, dict):
        raise RuntimeError("session_capsule_state_missing")
    return data


@contextmanager
def materialize_secret_capsule(value=None):
    """Yield a 0600 temporary storage-state file and securely remove it afterwards."""
    capsule = decode_capsule(value or os.environ.get("ANTHARES_SESSION_B64"))
    fd, name = tempfile.mkstemp(prefix="anthares-session-", suffix=".json")
    try:
        os.chmod(name, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(capsule["storage_state"], handle, separators=(",", ":"))
        yield Path(name), {
            "domain": capsule["domain"],
            "expires_at": capsule["expires_at"],
        }
    finally:
        try:
            path = Path(name)
            if path.exists():
                size = path.stat().st_size
                with path.open("r+b", buffering=0) as handle:
                    handle.write(b"\x00" * size)
                path.unlink(missing_ok=True)
        except OSError:
            pass
