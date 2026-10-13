"""Encrypted, chunked GitLab snapshot store for a stopped Chromium profile.

Only AES-GCM ciphertext is written to GitLab. A generation manifest is published
last, and restore falls back to the previous known-good generation. The module
never logs or returns cookies, storage, profile file contents, tokens or keys.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PROJECT = os.environ.get("GITLAB_STATE_PROJECT", "87307279")
BRANCH = os.environ.get("GITLAB_STATE_BRANCH", "browser-state")
CHUNK_SIZE = 3 * 1024 * 1024
MAX_ARCHIVE = 96 * 1024 * 1024
MIN_ARCHIVE = 32 * 1024
REQUIRED = (Path("Local State"), Path("Default/Preferences"))
EXCLUDES = {"Cache", "Code Cache", "GPUCache", "GrShaderCache", "ShaderCache", "Crashpad", "BrowserMetrics", "Safe Browsing", "SingletonLock", "SingletonSocket", "SingletonCookie"}


def slot():
    value = os.environ.get("GITLAB_STATE_SLOT", "runtime").strip()
    if not value or len(value) > 64 or not all(c.isalnum() or c in "-_" for c in value):
        raise RuntimeError("invalid_state_slot")
    return value


def configured():
    return bool(os.environ.get("GITLAB_TOKEN") and os.environ.get("GITLAB_STATE_KEY"))


def key():
    secret = os.environ.get("GITLAB_STATE_KEY", "").encode()
    if len(secret) < 32:
        raise RuntimeError("GITLAB_STATE_KEY must have at least 32 characters")
    return hashlib.pbkdf2_hmac("sha256", secret, b"anthares-browser-gitlab-state-v1", 250000, 32)


def request_file(path, method="GET", payload=None):
    project = urllib.parse.quote(PROJECT, safe="")
    url = "https://gitlab.com/api/v4/projects/" + project + "/repository/files/" + urllib.parse.quote(path, safe="")
    headers = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"], "Accept": "application/json"}
    if method == "GET":
        url += "?ref=" + urllib.parse.quote(BRANCH, safe="")
    else:
        headers["Content-Type"] = "application/json"
    body = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method=method), timeout=35) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"gitlab_state_http_{exc.code}") from exc


def put(path, blob, message):
    method = "PUT" if request_file(path) is not None else "POST"
    payload = {"branch": BRANCH, "commit_message": message, "content": base64.b64encode(blob).decode(), "encoding": "base64"}
    if not request_file(path, method, payload):
        raise RuntimeError("snapshot_write_failed")


def get(path):
    record = request_file(path)
    return None if record is None else base64.b64decode(record["content"])


def parse_manifest(raw):
    if not raw:
        return None
    try:
        value = json.loads(raw)
        generation = str(value["generation"])
        chunks = int(value["chunks"])
        size = int(value["bytes"])
        digest = str(value["sha256"]).lower()
    except (ValueError, TypeError, KeyError, UnicodeError):
        return None
    if value.get("version") != 1 or len(generation) != 24 or any(c not in "0123456789abcdef" for c in generation) or not (1 <= chunks <= 40) or not (MIN_ARCHIVE <= size <= MAX_ARCHIVE + 1024) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return None
    return {"version": 1, "generation": generation, "chunks": chunks, "bytes": size, "sha256": digest}


def initialized(profile):
    root = Path(profile)
    return all((root / rel).is_file() for rel in REQUIRED)


def archive_profile(profile):
    root = Path(profile)
    if not initialized(root):
        raise RuntimeError("profile_not_initialized")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root)
            if path.is_symlink() or any(part in EXCLUDES for part in rel.parts):
                continue
            if path.is_file():
                if path.stat().st_size > MAX_ARCHIVE:
                    continue
                archive.add(path, arcname=str(rel), recursive=False)
                if buf.tell() > MAX_ARCHIVE:
                    raise RuntimeError("profile_snapshot_too_large")
    raw = buf.getvalue()
    if len(raw) < MIN_ARCHIVE:
        raise RuntimeError("profile_snapshot_too_small")
    return raw


def backup(profile):
    if not configured():
        return {"ok": False, "reason": "not_configured"}
    try:
        raw = archive_profile(profile)
    except RuntimeError as exc:
        return {"ok": False, "reason": str(exc)[:80]}
    generation = secrets.token_hex(12)
    nonce = secrets.token_bytes(12)
    aad = slot().encode()
    encrypted = nonce + AESGCM(key()).encrypt(nonce, raw, aad)
    chunks = [encrypted[i:i + CHUNK_SIZE] for i in range(0, len(encrypted), CHUNK_SIZE)]
    base = f"browser-state/{slot()}/generations/{generation}"
    for index, chunk in enumerate(chunks):
        put(f"{base}/{index:03d}.bin", chunk, "state: encrypted Chromium profile chunk")
    for index, expected in enumerate(chunks):
        observed = get(f"{base}/{index:03d}.bin")
        if observed is None or not secrets.compare_digest(hashlib.sha256(observed).digest(), hashlib.sha256(expected).digest()):
            raise RuntimeError("snapshot_upload_verification_failed")
    manifest = {"version": 1, "generation": generation, "chunks": len(chunks), "sha256": hashlib.sha256(encrypted).hexdigest(), "bytes": len(encrypted)}
    latest = f"browser-state/{slot()}/latest.json"
    previous = f"browser-state/{slot()}/previous.json"
    previous_latest = get(latest)
    if parse_manifest(previous_latest) is not None:
        put(previous, previous_latest, "state: preserve previous Chromium profile manifest")
    put(latest, json.dumps(manifest, separators=(",", ":")).encode(), "state: commit encrypted Chromium profile generation")
    return {"ok": True, "generation": generation, "chunks": len(chunks), "bytes": len(encrypted)}


def decrypt_generation(raw_manifest):
    manifest = parse_manifest(raw_manifest)
    if manifest is None:
        raise RuntimeError("invalid_snapshot_manifest")
    base = f"browser-state/{slot()}/generations/{manifest['generation']}"
    chunks = []
    for index in range(manifest["chunks"]):
        chunk = get(f"{base}/{index:03d}.bin")
        if chunk is None:
            raise RuntimeError("incomplete_snapshot_generation")
        chunks.append(chunk)
    encrypted = b"".join(chunks)
    if len(encrypted) != manifest["bytes"] or hashlib.sha256(encrypted).hexdigest() != manifest["sha256"]:
        raise RuntimeError("snapshot_integrity_verification_failed")
    raw = AESGCM(key()).decrypt(encrypted[:12], encrypted[12:], slot().encode())
    if len(raw) > MAX_ARCHIVE:
        raise RuntimeError("snapshot_exceeds_maximum_size")
    return manifest, raw


def validate_archive(raw):
    archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    members = archive.getmembers()
    names = set()
    for member in members:
        name = Path(member.name)
        if name.is_absolute() or ".." in name.parts or not member.isfile() or member.issym() or member.islnk():
            archive.close()
            raise RuntimeError("unsafe_snapshot_entry")
        names.add(name.as_posix())
    if not {p.as_posix() for p in REQUIRED}.issubset(names):
        archive.close()
        raise RuntimeError("snapshot_profile_markers_missing")
    return archive, members


def extract_profile(raw, profile):
    archive, members = validate_archive(raw)
    destination = Path(profile)
    staging = destination.with_name(destination.name + ".restore-staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        for member in members:
            target = staging / Path(member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("snapshot_entry_unreadable")
            with source, target.open("wb") as out:
                shutil.copyfileobj(source, out)
    finally:
        archive.close()
    if not initialized(staging):
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError("restored_profile_not_initialized")
    old = destination.with_name(destination.name + ".restore-old")
    shutil.rmtree(old, ignore_errors=True)
    if destination.exists():
        destination.rename(old)
    staging.rename(destination)
    shutil.rmtree(old, ignore_errors=True)


def restore(profile):
    if not configured():
        return {"ok": False, "reason": "not_configured"}
    failures = []
    for source in ("latest", "previous"):
        raw_manifest = get(f"browser-state/{slot()}/{source}.json")
        if not raw_manifest:
            failures.append(f"{source}:missing")
            continue
        try:
            manifest, raw = decrypt_generation(raw_manifest)
            extract_profile(raw, profile)
            return {"ok": True, "generation": manifest["generation"], "source": source, "fallback_used": source == "previous"}
        except Exception as exc:
            failures.append(f"{source}:{str(exc)[:80]}")
    return {"ok": False, "reason": "no_valid_snapshot", "attempts": failures}
