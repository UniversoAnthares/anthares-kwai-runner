#!/usr/bin/env python3
"""KW-04: stage one queued MP4 on a remote Android without publishing media.

Trusted queue envelope: KWAI_QUEUE_JOB_ID, KWAI_VIDEO_URL, KWAI_EXPECTED_ACCOUNT.
An upstream content hash, when available, must be passed as
KWAI_EXPECTED_MEDIA_SHA256 (the queue's dispatch-identity hash is not a byte hash).
Outputs kwai-media-ready.json only after local/Android SHA-256 and MediaStore agree.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

MEDIA_DIR = "/sdcard/Movies/AntharesPublish"
MEDIA_URI = "content://media/external/video/media"
LIMIT = 250 * 1024 * 1024
PROOF = Path(os.getenv("KWAI_MEDIA_PROOF_FILE", "kwai-media-ready.json"))
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
JOB_RE = re.compile(r"^[A-Za-z0-9._:-]{3,160}$")


class StageError(RuntimeError):
    pass


def safe_public_https(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise StageError("source-requires-public-https")
    if parsed.port not in (None, 443):
        raise StageError("source-port-not-approved")
    host = parsed.hostname
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise StageError("source-local-host")
    try:
        addresses = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise StageError("source-dns-failure") from e
    if not addresses:
        raise StageError("source-dns-empty")
    for entry in addresses:
        try:
            addr = ipaddress.ip_address(entry[4][0].split("%", 1)[0])
        except ValueError as e:
            raise StageError("source-address-invalid") from e
        if not addr.is_global:
            raise StageError("source-private-address")


class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_public_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url: str, dest: Path, expected: str) -> tuple[str, int]:
    safe_public_https(url)
    opener = build_opener(PublicRedirect())
    digest = hashlib.sha256()
    total = 0
    try:
        response = opener.open(Request(url, headers={"User-Agent": "Anthares-Kwai-MediaStage/1.0"}), timeout=80)
    except Exception:
        raise StageError("source-fetch-failed") from None
    with response:
        if response.geturl() != url:
            safe_public_https(response.geturl())
        declared = response.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > LIMIT:
            raise StageError("source-too-large")
        with dest.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > LIMIT:
                    raise StageError("source-too-large")
                handle.write(chunk)
                digest.update(chunk)
    if total < 1024:
        raise StageError("source-empty-or-too-small")
    with dest.open("rb") as handle:
        handle.seek(4)
        if handle.read(4) != b"ftyp":
            raise StageError("source-not-mp4")
    got = digest.hexdigest()
    if expected and got != expected:
        raise StageError("source-sha256-mismatch")
    return got, total


def adb(*args: str, timeout: int = 45) -> str:
    proc = subprocess.run(["adb", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, text=True)
    if proc.returncode:
        raise StageError("adb-command-failed:" + args[0])
    return proc.stdout.strip()


def android_sha(path: str) -> str | None:
    proc = subprocess.run(["adb", "shell", "sha256sum", path], stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, timeout=45)
    if proc.returncode:
        return None
    found = proc.stdout.split()
    return found[0].lower() if found and SHA_RE.fullmatch(found[0].lower()) else None


def media_id(name: str, size: int, path: str) -> str:
    for attempt in range(15):
        query = subprocess.run(["adb", "shell", "content", "query", "--uri", MEDIA_URI,
                                "--projection", "_id:_display_name:_size:_data"],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, timeout=45)
        listing = query.stdout if query.returncode == 0 else ""
        matches = []
        for line in listing.replace("\r", "").splitlines():
            if not line.lstrip().startswith("Row:"):
                continue
            values = dict(re.findall(r"(?:^|[, ])(_id|_display_name|_size|_data)=([^,]+)", line))
            if (values.get("_display_name") == name and values.get("_size") == str(size)
                    and (not values.get("_data") or values["_data"].endswith("/" + name))):
                matches.append(values.get("_id", ""))
        if len(matches) == 1 and matches[0].isdigit():
            return matches[0]
        if len(matches) > 1:
            raise StageError("mediastore-ambiguous-identity")
        if attempt != 14:
            subprocess.run(["adb", "shell", "am", "broadcast", "-a",
                            "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                            "-d", "file://" + path], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=20)
            time.sleep(2)
    raise StageError("mediastore-index-timeout")


def main() -> int:
    job = os.getenv("KWAI_QUEUE_JOB_ID", "").strip()
    url = os.getenv("KWAI_VIDEO_URL", "").strip()
    account = os.getenv("KWAI_EXPECTED_ACCOUNT", "").strip().lstrip("@").lower()
    expected = os.getenv("KWAI_EXPECTED_MEDIA_SHA256", "").strip().lower()
    if not JOB_RE.fullmatch(job) or not account or not url:
        raise StageError("queue-identity-incomplete")
    if not re.fullmatch(r"[a-z0-9._]{3,80}", account):
        raise StageError("account-invalid")
    if expected and not SHA_RE.fullmatch(expected):
        raise StageError("expected-sha256-invalid")
    if PROOF.exists():
        raise StageError("existing-stage-proof-refuses-reuse")
    with tempfile.TemporaryDirectory(prefix="kwai-media-", dir=os.getenv("RUNNER_TEMP") or None) as tmp:
        src = Path(tmp) / "media.mp4"
        digest, size = download(url, src, expected)
        token = re.sub(r"[^a-zA-Z0-9._-]", "_", job)[:64]
        name = f"anthares-{token}-{digest[:20]}.mp4"
        remote = f"{MEDIA_DIR}/{name}"
        adb("wait-for-device", timeout=90)
        adb("shell", "mkdir", "-p", MEDIA_DIR)
        current = android_sha(remote)
        if current is None:
            adb("push", str(src), remote, timeout=240)
            current = android_sha(remote)
        if current != digest:
            raise StageError("android-sha256-mismatch")
        count = media_id(name, size, remote)
        payload = {"schema": "anthares.kwai.media-ready.v1", "job_id": job, "account": account,
                   "sha256": digest, "size": size, "name": name, "remote_path": remote,
                   "media_store_id": count, "media_uri": MEDIA_URI + "/" + count,
                   "source_id": os.getenv("KWAI_SOURCE_ID", ""),
                   "source_start": os.getenv("KWAI_SOURCE_START", ""),
                   "source_end": os.getenv("KWAI_SOURCE_END", "")}
        PROOF.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        PROOF.chmod(0o600)
        print("KWAI_MEDIA_STAGE=READY")
        print("KWAI_MEDIA_SHA256=" + digest)
        print("KWAI_MEDIA_SIZE=" + str(size))
        print("KWAI_MEDIA_NAME=" + name)
        print("KWAI_ANDROID_VIDEO=" + remote)
        print("KWAI_ANDROID_MEDIA_URI=" + payload["media_uri"])
        print("KWAI_MEDIASTORE_MATCHES=1")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StageError, OSError, subprocess.TimeoutExpired) as exc:
        print("KWAI_MEDIA_STAGE=FAILED_SAFE reason=" + str(exc).splitlines()[0][:160],
              file=sys.stderr)
        raise SystemExit(82)
