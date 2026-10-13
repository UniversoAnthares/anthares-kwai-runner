"""Encrypted, chunked GitLab snapshot store for a stopped Chromium profile.

Only enabled when GITLAB_TOKEN and CONTROL_TOKEN are set. No plaintext
profile material is sent to GitLab; uploads are AES-GCM authenticated.
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
SLOT = os.environ.get("GITLAB_STATE_SLOT", "runtime")
CHUNK_SIZE = 3 * 1024 * 1024
MAX_ARCHIVE = 96 * 1024 * 1024
EXCLUDES = {"Cache", "Code Cache", "GPUCache", "GrShaderCache", "ShaderCache",
            "Crashpad", "BrowserMetrics", "Safe Browsing", "SingletonLock",
            "SingletonSocket", "SingletonCookie"}

def configured():
    return bool(os.environ.get("GITLAB_TOKEN") and os.environ.get("CONTROL_TOKEN"))

def _key():
    secret = os.environ["CONTROL_TOKEN"].encode()
    if len(secret) < 32:
        raise RuntimeError("CONTROL_TOKEN must have at least 32 characters")
    return hashlib.pbkdf2_hmac("sha256", secret,
                              b"anthares-browser-gitlab-state-v1", 250000, 32)

def _request(path, method="GET", payload=None):
    project = urllib.parse.quote(PROJECT, safe="")
    url = "https://gitlab.com/api/v4/projects/" + project + "/repository/files/" + urllib.parse.quote(path, safe="")
    headers = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"], "Accept": "application/json"}
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
    payload = {"branch": BRANCH, "commit_message": message,
               "content": base64.b64encode(blob).decode(), "encoding": "base64"}
    result = _request(path, method, payload)
    if not result:
        raise RuntimeError("GitLab snapshot write did not return a result")

def _get(path):
    record = _request(path)
    if record is None:
        return None
    return base64.b64decode(record["content"])

def _archive(profile):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        for p in sorted(Path(profile).rglob("*")):
            rel = p.relative_to(profile)
            if any(part in EXCLUDES for part in rel.parts) or p.is_symlink():
                continue
            if p.is_file() and p.stat().st_size <= MAX_ARCHIVE:
                archive.add(p, arcname=str(rel), recursive=False)
                if buf.tell() > MAX_ARCHIVE:
                    raise RuntimeError("profile snapshot exceeds 96 MiB limit")
    return buf.getvalue()

def backup(profile):
    if not configured():
        return {"ok": False, "reason": "not_configured"}
    raw = _archive(Path(profile))
    generation = secrets.token_hex(12)
    nonce = secrets.token_bytes(12)
    encrypted = nonce + AESGCM(_key()).encrypt(nonce, raw, SLOT.encode())
    chunks = [encrypted[i:i + CHUNK_SIZE] for i in range(0, len(encrypted), CHUNK_SIZE)]
    base = f"browser-state/{SLOT}/generations/{generation}"
    for index, chunk in enumerate(chunks):
        _put(f"{base}/{index:03d}.bin", chunk, "state: encrypted Chromium profile chunk")
    manifest = {"version": 1, "generation": generation, "chunks": len(chunks),
                "sha256": hashlib.sha256(encrypted).hexdigest(), "bytes": len(encrypted)}
    # Manifest written LAST: readers never observe an incomplete generation.
    _put(f"browser-state/{SLOT}/latest.json",
         json.dumps(manifest, separators=(",", ":")).encode(),
         "state: commit encrypted Chromium profile generation")
    return {"ok": True, "chunks": len(chunks), "bytes": len(encrypted)}

def restore(profile):
    if not configured():
        return {"ok": False, "reason": "not_configured"}
    manifest_raw = _get(f"browser-state/{SLOT}/latest.json")
    if not manifest_raw:
        return {"ok": False, "reason": "no_snapshot"}
    try:
        manifest = json.loads(manifest_raw)
    except (ValueError, TypeError):
        return {"ok": False, "reason": "no_snapshot"}
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        return {"ok": False, "reason": "no_snapshot"}
    generation = manifest["generation"]
    count = int(manifest["chunks"])
    if not (1 <= count <= 40):
        raise RuntimeError("invalid chunk count")
    chunks = []
    for i in range(count):
        chunk = _get(f"browser-state/{SLOT}/generations/{generation}/{i:03d}.bin")
        if chunk is None:
            raise RuntimeError("incomplete snapshot generation")
        chunks.append(chunk)
    encrypted = b"".join(chunks)
    if len(encrypted) != manifest["bytes"] or hashlib.sha256(encrypted).hexdigest() != manifest["sha256"]:
        raise RuntimeError("snapshot integrity verification failed")
    raw = AESGCM(_key()).decrypt(encrypted[:12], encrypted[12:], SLOT.encode())
    if len(raw) > MAX_ARCHIVE:
        raise RuntimeError("snapshot exceeds maximum size")
    destination = Path(profile)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive.getmembers():
            name = Path(member.name)
            if (name.is_absolute() or ".." in name.parts or
                not member.isfile() or member.issym() or member.islnk()):
                raise RuntimeError("unsafe snapshot entry")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open("wb") as out:
                import shutil
                shutil.copyfileobj(source, out)
    return {"ok": True, "generation": generation}

if __name__ == "__main__":
    import sys
    operation = sys.argv[1]
    if operation not in ("backup", "restore"):
        raise SystemExit("usage: profile_store.py backup|restore")
    print(json.dumps(globals()[operation](os.environ.get("CHROME_PROFILE_DIR", "/data/chrome-profile"))))
