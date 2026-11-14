#!/usr/bin/env python3
"""Verify an original Kwai universal APK, then optionally register at SpawnDroid.

Cloud-runner only. No APK rebuilding, resigning, local-PC staging, Android
session, login, publication or production cutover. Fail closed on ambiguity.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

EXPECTED_PACKAGE = "com.kwai.video"
EXPECTED_CERT_SHA256 = "bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047"
MAX_BYTES = 512 * 1024 * 1024
API_ROOT = "https://app.spawndroid.io"


class ValidationError(ValueError):
    """Sanitized failure; never print HTTP responses or signed upload URLs."""


def _tool(env_name: str, default: str) -> str:
    path = os.environ.get(env_name) or shutil.which(default)
    if not path:
        raise ValidationError(f"missing_{default}_tool")
    return path


def _run(argv: list[str]) -> str:
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValidationError("android_tool_unavailable") from None
    if p.returncode != 0:
        raise ValidationError("android_signature_or_manifest_invalid")
    return p.stdout + "\n" + p.stderr


def parse_aapt(text: str) -> tuple[str, int, str, tuple[str, ...]]:
    m = re.search(r"(?m)^package:\s+name='([^']+)'\s+versionCode='(\d+)'\s+versionName='([^']*)'", text)
    if not m:
        raise ValidationError("package_manifest_unreadable")
    native = re.search(r"(?m)^native-code:\s+(.+)$", text)
    arches = tuple(re.findall(r"'([^']+)'", native.group(1))) if native else ()
    return m.group(1), int(m.group(2)), m.group(3), arches


def parse_apksigner(text: str) -> str:
    signers = re.findall(
        r"(?mi)^Signer #\d+ certificate SHA-256 digest:\s*([0-9a-f: ]+)$", text
    )
    normalized = {re.sub(r"[^0-9a-f]", "", v.lower()) for v in signers}
    if len(normalized) != 1:
        raise ValidationError("unexpected_signer_count")
    cert = next(iter(normalized))
    if not re.fullmatch(r"[0-9a-f]{64}", cert):
        raise ValidationError("invalid_certificate_digest")
    schemes = re.findall(
        r"(?mi)^Verified using v([23]) scheme(?:\s*\([^)]*\))?:\s*(true|false)\s*$",
        text,
    )
    if not any(value.lower() == "true" for _, value in schemes):
        raise ValidationError("apk_v2_v3_signature_required")
    return cert


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_apk(path: Path, expected_sha256: str, *,
               min_version_code: int = 647004) -> dict:
    if path.suffix.lower() != ".apk" or not path.is_file() or path.is_symlink():
        raise ValidationError("single_apk_required")
    size = path.stat().st_size
    if not 1_000_000 <= size <= MAX_BYTES:
        raise ValidationError("apk_size_out_of_bounds")
    expected = expected_sha256.lower().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValidationError("expected_sha256_invalid")
    actual = sha256_file(path)
    if not hmac.compare_digest(actual, expected):
        raise ValidationError("binary_sha256_mismatch")
    try:
        with zipfile.ZipFile(path) as apk:
            entries = apk.namelist()
            if "AndroidManifest.xml" not in entries or not any(
                    re.fullmatch(r"classes\d*\.dex", n) for n in entries):
                raise ValidationError("apk_structure_invalid")
            if apk.testzip() is not None:
                raise ValidationError("apk_zip_integrity_failed")
    except (zipfile.BadZipFile, OSError):
        raise ValidationError("apk_zip_integrity_failed") from None
    package, version_code, version_name, arches = parse_aapt(
        _run([_tool("ANDROID_AAPT", "aapt"), "dump", "badging", str(path)])
    )
    if package != EXPECTED_PACKAGE:
        raise ValidationError("wrong_android_package")
    if version_code < min_version_code:
        raise ValidationError("obsolete_version_requires_new_review")
    if arches and "arm64-v8a" not in arches:
        raise ValidationError("arm64_not_supported")
    cert = parse_apksigner(_run([
        _tool("ANDROID_APKSIGNER", "apksigner"), "verify", "--verbose",
        "--print-certs", str(path),
    ]))
    if not hmac.compare_digest(cert, EXPECTED_CERT_SHA256):
        raise ValidationError("official_certificate_mismatch")
    return {
        "package": package, "versionCode": version_code,
        "versionName": version_name, "size": size,
        "sha256": actual, "certificate_sha256": cert,
        "architecture": list(arches),
        "signature": "apksigner_v2_or_v3_verified",
    }


def _json_api(method: str, path: str, key: str, body: dict | None = None) -> dict:
    if not path.startswith("/api/"):
        raise ValidationError("invalid_api_path")
    data = json.dumps(body).encode("utf8") if body is not None else None
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API_ROOT + path, method=method,
                                 data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            parsed = json.loads(resp.read(65536))
            if not isinstance(parsed, dict):
                raise ValidationError("api_response_invalid")
            return parsed
    except urllib.error.HTTPError as exc:
        raise ValidationError("spawndroid_http_" + str(exc.code)) from None
    except (OSError, ValueError):
        raise ValidationError("api_result_uncertain_reconcile_required") from None


def _server_package(value: dict) -> str:
    for source in (value, value.get("manifest"), value.get("parsed")):
        if isinstance(source, dict):
            pkg = source.get("packageName") or source.get("package")
            if isinstance(pkg, dict):
                pkg = pkg.get("name")
            if isinstance(pkg, str) and pkg:
                return pkg
    return ""


def register_verified(path: Path, evidence: dict, *, key: str) -> str:
    """One attempt only. Any uncertain write forbids automatic retry."""
    if os.environ.get("SPAWNDROID_REGISTER_APPROVED") != "1" or not key:
        raise ValidationError("registration_authorization_or_key_missing")
    before = _json_api("GET", "/api/apps", key).get("apps")
    if not isinstance(before, list):
        raise ValidationError("workspace_inventory_unverified")
    for app in before:
        if isinstance(app, dict) and _server_package(app) == EXPECTED_PACKAGE:
            versions = app.get("versions")
            if isinstance(versions, list) and any(
                str(v.get("versionCode")) == str(evidence["versionCode"])
                for v in versions if isinstance(v, dict)
            ):
                raise ValidationError("same_version_already_registered_check_existing")
    presign = _json_api("POST", "/api/apps/presign", key, {
        "filename": path.name, "size": evidence["size"],
    })
    signed_url = presign.get("url")
    storage_key = presign.get("key")
    media = presign.get("contentType")
    if not all(isinstance(v, str) and v for v in (signed_url, storage_key, media)):
        raise ValidationError("upload_presign_invalid")
    u = urllib.parse.urlparse(signed_url)
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        raise ValidationError("upload_destination_invalid")
    if not re.fullmatch(r"[a-zA-Z0-9/_.-]+", storage_key) or ".." in storage_key:
        raise ValidationError("upload_storage_key_invalid")
    # PUT bytes to provider's *issued* presigned destination. No token is printed.
    try:
        req = urllib.request.Request(
            signed_url, method="PUT", data=path.read_bytes(),
            headers={"Content-Type": media},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            if not 200 <= resp.status < 300:
                raise ValidationError("upload_not_confirmed")
    except (OSError, urllib.error.HTTPError):
        raise ValidationError("upload_uncertain_reconcile_required") from None
    created = _json_api("POST", "/api/apps", key, {
        "key": storage_key, "filename": path.name,
    })
    app = created.get("app")
    parsed = created.get("parsed")
    if not isinstance(app, dict):
        raise ValidationError("registration_uncertain_reconcile_required")
    if _server_package(app) != EXPECTED_PACKAGE and (
            not isinstance(parsed, dict) or _server_package(parsed) != EXPECTED_PACKAGE):
        raise ValidationError("registered_package_unverified")
    slug = app.get("slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-zA-Z0-9._-]{3,128}", slug):
        raise ValidationError("registration_slug_missing")
    after = _json_api("GET", "/api/apps", key).get("apps")
    if not isinstance(after, list) or not any(
            isinstance(x, dict) and x.get("slug") == slug
            and _server_package(x) == EXPECTED_PACKAGE for x in after):
        raise ValidationError("registration_readback_unverified")
    return slug


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--min-version-code", type=int, default=647004)
    parser.add_argument("--register", action="store_true")
    args = parser.parse_args()
    try:
        evidence = verify_apk(args.apk, args.sha256,
                              min_version_code=args.min_version_code)
        print("KWAI_APK_VALIDATED=" + json.dumps(evidence, sort_keys=True))
        if args.register:
            slug = register_verified(
                args.apk, evidence, key=os.environ.get("SPAWNDROID_API_KEY", ""))
            print("SPAWNDROID_KWAI_ARTIFACT_SLUG=" + slug)
            print("SPAWNDROID_UPLOAD_READBACK=PASS")
        else:
            print("SPAWNDROID_UPLOAD_READBACK=NOT_ATTEMPTED")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 0
    except ValidationError as exc:
        print("KWAI_APK_GUARD=" + str(exc))
        print("SPAWNDROID_UPLOAD_READBACK=NOT_PROVEN")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25


if __name__ == "__main__":
    sys.exit(main())
