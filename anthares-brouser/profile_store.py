"""Encrypted, chunked GitLab snapshot store for a stopped Chromium profile.

No plaintext profile material is sent to GitLab. Snapshots are AES-GCM
authenticated. The store is fail-closed: an uninitialised/empty Chromium profile
is never allowed to replace a valid snapshot, and restore falls back to the
previous committed manifest when the newest generation is incomplete/corrupt.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PROJECT = os.environ.get("GITLAB_STATE_PROJECT", "87307279")
BRANCH = os.environ.get("GITLAB_STATE_BRANCH", "browser-state")


def _slot():
    return os.environ.get("GITLAB_STATE_SLOT", "runtime")


CHUNK_SIZE = 3 * 1024 * 1024
MAX_ARCHIVE = 96 * 1024 * 1024
MIN_ARCHIVE = 32 * 1024
REQUIRED_PROFILE_FILES = (Path("Local State"), Path("Default/Preferences"))
EXCLUDES = {
    "Cache", "Code Cache", "GPUCache", "GrShaderCache", "ShaderCache",
    "Crashpad", "BrowserMetrics", "Safe Browsing", "SingletonLock",
    "SingletonSocket", "SingletonCookie",
}


def _state_secret():
    return os.environ.get("GITLAB_STATE_KEY") or os.environ.get("CONTROL_TOKEN") or ""


def configured():
    return bool(os.environ.get("GITLAB_TOKEN") and _state_secret())


def _key():
    secret = _state_secret().encode()
    if len(secret) < 32:
        raise RuntimeError("GITLAB_STATE_KEY must have at least 32 characters")
    return hashlib.pbkdf2_hmac(
        "sha256", secret, b"anthares-browser-gitlab-state-v1", 250000, 32
    )


def _request(path, method="GET", payload=None):
    project = urllib.parse.quote(PROJECT, safe="")
    url = (
        "https://gitlab.com/api/v4/projects/" + project + "/repository/files/"
        + urllib.parse.quote(path, safe="")
    )
    headers = {
        "PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"],
        "Accept": "application/json",
    }
    if method == "GET":
        url += "?ref=" + urllib.parse.quote(BRANCH, safe="")
    else:
        headers["Content-Type"] = "application/json"
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"GitLab state request failed: HTTP {exc.code}") from exc


def _put(path, blob, message):
    exists = _request(path) is not None
    method = "PUT" if exists else "POST"
    payload = {
        "branch": BRANCH,
        "commit_message": message,
        "content": base64.b64encode(blob).decode(),
        "encoding": "base64",
    }
    result = _request(path, method, payload)
    if not result:
        raise RuntimeError("GitLab snapshot write did not return a result")


def _get(path):
    record = _request(path)
    if record is None:
        return None
    return base64.b64decode(record["content"])


def _manifest(raw):
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (ValueError, TypeError, UnicodeError):
        return None
    if not isinstance(value, dict) or value.get("version") != 1:
        return None
    try:
        generation = str(value["generation"])
        chunks = int(value["chunks"])
        size = int(value["bytes"])
        digest = str(value["sha256"])
    except (KeyError, TypeError, ValueError):
        return None
    if (
        len(generation) != 24
        or not all(c in "0123456789abcdef" for c in generation)
        or not (1 <= chunks <= 40)
        or size < MIN_ARCHIVE
        or size > MAX_ARCHIVE + 1024
        or len(digest) != 64
        or not all(c in "0123456789abcdef" for c in digest.lower())
    ):
        return None
    return {
        "version": 1,
        "generation": generation,
        "chunks": chunks,
        "sha256": digest.lower(),
        "bytes": size,
    }


def _profile_initialized(profile: Path):
    return all((profile / rel).is_file() for rel in REQUIRED_PROFILE_FILES)


def _archive(profile):
    profile = Path(profile)
    if not _profile_initialized(profile):
        raise RuntimeError("profile_not_initialized")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        for p in sorted(profile.rglob("*")):
            rel = p.relative_to(profile)
            if any(part in EXCLUDES for part in rel.parts) or p.is_symlink():
                continue
            if p.is_file() and p.stat().st_size <= MAX_ARCHIVE:
                archive.add(p, arcname=str(rel), recursive=False)
                if buf.tell() > MAX_ARCHIVE:
                    raise RuntimeError("profile snapshot exceeds 96 MiB limit")
    raw = buf.getvalue()
    if len(raw) < MIN_ARCHIVE:
        raise RuntimeError("profile_snapshot_too_small")
    return raw


def _validate_uploaded_generation(base, chunks):
    for index, expected in enumerate(chunks):
        observed = _get(f"{base}/{index:03d}.bin")
        if observed is None or not hashlib.sha256(observed).digest() == hashlib.sha256(expected).digest():
            raise RuntimeError("snapshot upload verification failed")


def backup(profile):
    if not configured():
        return {"ok": False, "reason": "not_configured"}
    try:
        raw = _archive(Path(profile))
    except RuntimeError as exc:
        if str(exc) in {"profile_not_initialized", "profile_snapshot_too_small"}:
            return {"ok": False, "reason": str(exc)}
        raise

    generation = secrets.token_hex(12)
    nonce = secrets.token_bytes(12)
    encrypted = nonce + AESGCM(_key()).encrypt(nonce, raw, _slot().encode())
    chunks = [
        encrypted[i:i + CHUNK_SIZE]
        for i in range(0, len(encrypted), CHUNK_SIZE)
    ]
    base = f"browser-state/{_slot()}/generations/{generation}"
    for index, chunk in enumerate(chunks):
        _put(
            f"{base}/{index:03d}.bin", chunk,
            "state: encrypted Chromium profile chunk",
        )

    # Verify what GitLab can read before publishing a manifest that points at it.
    _validate_uploaded_generation(base, chunks)
    manifest = {
        "version": 1,
        "generation": generation,
        "chunks": len(chunks),
        "sha256": hashlib.sha256(encrypted).hexdigest(),
        "bytes": len(encrypted),
    }
    manifest_blob = json.dumps(manifest, separators=(",", ":")).encode()
    latest_path = f"browser-state/{_slot()}/latest.json"
    previous_path = f"browser-state/{_slot()}/previous.json"

    # Keep one known-good manifest. Invalid/tiny manifests are never promoted.
    previous_latest = _get(latest_path)
    if _manifest(previous_latest) is not None:
        _put(
            previous_path, previous_latest,
            "state: preserve previous Chromium profile manifest",
        )

    # Manifest is written LAST: readers never intentionally observe an
    # incomplete generation. Restore still has previous.json as a race fallback.
    _put(
        latest_path, manifest_blob,
        "state: commit encrypted Chromium profile generation",
    )
    return {
        "ok": True,
        "chunks": len(chunks),
        "bytes": len(encrypted),
        "generation": generation,
    }


def _decrypt_manifest(manifest_raw):
    manifest = _manifest(manifest_raw)
    if manifest is None:
        raise RuntimeError("invalid_snapshot_manifest")
    generation = manifest["generation"]
    chunks = []
    for i in range(manifest["chunks"]):
        chunk = _get(
            f"browser-state/{_slot()}/generations/{generation}/{i:03d}.bin"
        )
        if chunk is None:
            raise RuntimeError("incomplete_snapshot_generation")
        chunks.append(chunk)
    encrypted = b"".join(chunks)
    if (
        len(encrypted) != manifest["bytes"]
        or hashlib.sha256(encrypted).hexdigest() != manifest["sha256"]
    ):
        raise RuntimeError("snapshot_integrity_verification_failed")
    raw = AESGCM(_key()).decrypt(
        encrypted[:12], encrypted[12:], _slot().encode()
    )
    if len(raw) > MAX_ARCHIVE:
        raise RuntimeError("snapshot_exceeds_maximum_size")
    return manifest, raw


def _validated_members(raw):
    archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    members = archive.getmembers()
    names = set()
    for member in members:
        name = Path(member.name)
        if (
            name.is_absolute()
            or ".." in name.parts
            or not member.isfile()
            or member.issym()
            or member.islnk()
        ):
            archive.close()
            raise RuntimeError("unsafe_snapshot_entry")
        names.add(name.as_posix())
    required = {p.as_posix() for p in REQUIRED_PROFILE_FILES}
    if not required.issubset(names):
        archive.close()
        raise RuntimeError("snapshot_profile_markers_missing")
    return archive, members


def _extract(raw, profile):
    archive, members = _validated_members(raw)
    destination = Path(profile)
    destination.mkdir(parents=True, exist_ok=True)
    try:
        for member in members:
            target = destination / Path(member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("snapshot_entry_unreadable")
            with source, target.open("wb") as out:
                import shutil
                shutil.copyfileobj(source, out)
    finally:
        archive.close()
    if not _profile_initialized(destination):
        raise RuntimeError("restored_profile_not_initialized")


def restore(profile):
    if not configured():
        return {"ok": False, "reason": "not_configured"}

    latest_path = f"browser-state/{_slot()}/latest.json"
    previous_path = f"browser-state/{_slot()}/previous.json"
    failures = []
    for source, path in (("latest", latest_path), ("previous", previous_path)):
        raw_manifest = _get(path)
        if not raw_manifest:
            failures.append(f"{source}:missing")
            continue
        try:
            manifest, raw = _decrypt_manifest(raw_manifest)
            _extract(raw, profile)
            return {
                "ok": True,
                "generation": manifest["generation"],
                "source": source,
                "fallback_used": source == "previous",
            }
        except Exception as exc:
            # Do not expose profile material or secrets in logs; only bounded
            # error class/reason is returned to the supervisor.
            failures.append(f"{source}:{str(exc)[:80]}")

    return {
        "ok": False,
        "reason": "no_valid_snapshot",
        "attempts": failures,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2 or sys.argv[1] not in ("backup", "restore"):
        raise SystemExit("usage: profile_store.py backup|restore")
    operation = sys.argv[1]
    result = globals()[operation](
        os.environ.get("CHROME_PROFILE_DIR", "/data/chrome-profile")
    )
    print(json.dumps(result, separators=(",", ":")))
    if not result.get("ok"):
        raise SystemExit(3)
