#!/usr/bin/env python3
"""Fail-closed preflight for ORIGINAL Kwai split APKs installed with Appium.

Alternative to the SpawnDroid build-upload path. Appium UiAutomator2 supports
"mobile: installMultipleApks", but access to that command on SpawnDroid has
NOT been proven. A CI/Android session must be acquired by the existing Agent02
coordinator. No Android is started, credentials copied, or video uploaded here.

All components must have the original publisher signature; never recombine,
rebuild, patch, or resign APKs. Downloads may only take place in an ephemeral
GitHub-hosted runner, never on the owner's computer.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

import kwai_spawndroid_apk_guard as guard

EXPECTED_COUNTS = {"com.kwai.video": 25, "kwai.lite.video": 18}
MAX_COMPONENT_BYTES = 170 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
NAME_RE = re.compile(r"^(?:base|split_[A-Za-z0-9_.-]+)\.apk$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
VERSION_MAX = 100_000_000


class SplitError(ValueError):
    pass


def _validated_https(url: str, domains: set[str]) -> str:
    if not isinstance(url, str) or len(url) > 4096:
        raise SplitError("component_url_invalid")
    u = urllib.parse.urlsplit(url)
    if (u.scheme != "https" or not u.hostname or u.username or u.password
            or u.port not in (None, 443) or u.fragment
            or u.hostname.lower() not in domains):
        raise SplitError("component_url_host_denied")
    if not u.path.lower().endswith(".apk"):
        raise SplitError("component_url_not_direct_apk")
    return url


def validate_manifest(doc: object, allowed_hosts: set[str]) -> dict:
    """Validate a manifest with immutable original hashes and HTTPS URLs."""
    if not isinstance(doc, dict):
        raise SplitError("manifest_invalid")
    pkg = doc.get("package")
    if pkg not in EXPECTED_COUNTS:
        raise SplitError("package_not_allowed")
    version = doc.get("versionCode")
    if type(version) is not int or not 1 <= version <= VERSION_MAX:
        raise SplitError("version_invalid")
    components = doc.get("files")
    if not isinstance(components, list) or len(components) != EXPECTED_COUNTS[pkg]:
        raise SplitError("split_count_incomplete")
    if not isinstance(allowed_hosts, set) or not allowed_hosts:
        raise SplitError("allowed_asset_hosts_missing")
    names = set()
    urls = set()
    total = 0
    result = []
    for item in components:
        if not isinstance(item, dict):
            raise SplitError("component_invalid")
        name = item.get("name")
        size = item.get("bytes")
        sha = item.get("sha256")
        url = item.get("url")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise SplitError("component_filename_invalid")
        if name in names:
            raise SplitError("duplicate_split_filename")
        names.add(name)
        if type(size) is not int or not 1024 <= size <= MAX_COMPONENT_BYTES:
            raise SplitError("component_size_invalid")
        if not isinstance(sha, str) or not HASH_RE.fullmatch(sha):
            raise SplitError("component_sha256_invalid")
        url = _validated_https(url, allowed_hosts)
        if url in urls:
            raise SplitError("duplicate_split_url")
        urls.add(url)
        total += size
        result.append({"name": name, "bytes": size, "sha256": sha, "url": url})
    if "base.apk" not in names or total > MAX_TOTAL_BYTES:
        raise SplitError("base_missing_or_total_oversize")
    return {"package": pkg, "versionCode": version, "bytes": total,
            "files": sorted(result, key=lambda x: (x["name"] != "base.apk", x["name"]))}


def _read_verified_component(entry: dict, destination: Path, allow_hosts: set[str]) -> None:
    """Fetch a single signed APK and validate hash, package, version, cert."""
    request = urllib.request.Request(entry["url"], headers={
        "Accept": "application/vnd.android.package-archive,application/octet-stream",
    })
    digest = hashlib.sha256()
    count = 0
    try:
        with urllib.request.urlopen(request, timeout=45) as resp:
            _validated_https(resp.geturl(), allow_hosts)
            with destination.open("wb") as output:
                while True:
                    chunk = resp.read(1048576)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > entry["bytes"]:
                        raise SplitError("split_size_exceeded")
                    digest.update(chunk)
                    output.write(chunk)
    except SplitError:
        raise
    except (OSError, ValueError):
        raise SplitError("split_download_failed_or_uncertain") from None
    if count != entry["bytes"] or not hmac.compare_digest(digest.hexdigest(), entry["sha256"]):
        raise SplitError("split_size_or_hash_mismatch")


def verify_component(path: Path, *, package: str, version: int) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            if "AndroidManifest.xml" not in archive.namelist():
                raise SplitError("split_manifest_missing")
            if archive.testzip() is not None:
                raise SplitError("split_zip_corrupt")
    except (zipfile.BadZipFile, OSError):
        raise SplitError("split_zip_corrupt") from None
    try:
        badges = guard._run([guard._tool("ANDROID_AAPT", "aapt"),
                             "dump", "badging", str(path)])
        p, v, _, _ = guard.parse_aapt(badges)
        if p != package or v != version:
            raise SplitError("split_package_or_version_mismatch")
        cert = guard.parse_apksigner(guard._run([
            guard._tool("ANDROID_APKSIGNER", "apksigner"), "verify",
            "--verbose", "--print-certs", str(path)
        ]))
    except guard.ValidationError:
        raise SplitError("split_signature_or_manifest_unverified") from None
    if not hmac.compare_digest(cert, guard.EXPECTED_CERT_SHA256):
        raise SplitError("publisher_certificate_mismatch")
    return cert


def audit_downloaded_set(doc: dict, directory: Path) -> dict:
    """Validate every APK; no installation is attempted."""
    for entry in doc["files"]:
        f = directory / entry["name"]
        if not f.is_file() or f.is_symlink():
            raise SplitError("split_missing")
        if f.stat().st_size != entry["bytes"]:
            raise SplitError("split_size_mismatch")
        if not hmac.compare_digest(guard.sha256_file(f), entry["sha256"]):
            raise SplitError("split_sha256_mismatch")
        verify_component(f, package=doc["package"], version=doc["versionCode"])
    return {"package": doc["package"], "versionCode": doc["versionCode"],
            "count": len(doc["files"]), "bytes": doc["bytes"],
            "cert": guard.EXPECTED_CERT_SHA256, "signed_splits_verified": True}


def download_and_verify(doc: dict, hosts: set[str], destination: Path) -> dict:
    for entry in doc["files"]:
        _read_verified_component(entry, destination / entry["name"], hosts)
    return audit_downloaded_set(doc, destination)


def webdriver_script(executor, package: str, version: int, urls: list[str]) -> dict:
    """Called ONLY inside an already-owned Appium 3 session.

    executor(script, args) is supplied by Agent02's session lifecycle; this
    function neither creates nor disposes an Android runner.
    """
    if os.environ.get("SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED") != "1":
        raise SplitError("appium_canary_not_authorized")
    if package not in EXPECTED_COUNTS:
        raise SplitError("package_not_allowed")
    if not urls or len(urls) != EXPECTED_COUNTS[package]:
        raise SplitError("split_urls_incomplete")
    executor("mobile: installMultipleApks", {
        "apks": urls,
        "options": {"grantPermissions": False, "replace": False,
                    "timeout": 180000},
    })
    installed = executor("mobile: isAppInstalled", {"appId": package})
    if installed is not True:
        raise SplitError("remote_install_not_confirmed")
    apps = executor("mobile: listApps", {})
    if not isinstance(apps, dict) or package not in apps:
        raise SplitError("remote_package_readback_unavailable")
    value = apps[package]
    if not isinstance(value, dict) or str(value.get("versionCode")) != str(version):
        raise SplitError("remote_version_unverified")
    return {"installed": True, "package": package, "versionCode": version,
            "publication_attempted": False, "login_attempted": False,
            "provider_session_closed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--mode", choices=("validate-manifest", "audit-cloud"),
                        default="validate-manifest")
    args = parser.parse_args()
    try:
        if not args.manifest.is_file():
            raise SplitError("manifest_missing")
        hosts = {x.strip().lower() for x in
                 os.environ.get("KWAI_APPROVED_APK_SOURCE_HOSTS", "").split(",")
                 if x.strip()}
        doc = validate_manifest(json.loads(args.manifest.read_text("utf8")), hosts)
        print("KWAI_ORIGINAL_SPLIT_MANIFEST_VALID=PASS")
        print("KWAI_PACKAGE=" + doc["package"])
        print("KWAI_APK_SPLIT_COUNT=" + str(len(doc["files"])))
        if args.mode == "audit-cloud":
            if not os.environ.get("RUNNER_TEMP") or os.environ.get("GITHUB_ACTIONS") != "true":
                raise SplitError("cloud_only_execution_required")
            with tempfile.TemporaryDirectory(prefix="kwai-apk-", dir=os.environ["RUNNER_TEMP"]) as tmp:
                receipt = download_and_verify(doc, hosts, Path(tmp))
                print("KWAI_ORIGINAL_SPLIT_CRYPTOGRAPHIC_VERIFICATION=" +
                      ("PASS" if receipt["signed_splits_verified"] else "FAILED"))
        else:
            print("KWAI_ORIGINAL_SPLIT_CRYPTOGRAPHIC_VERIFICATION=NOT_RUN")
        print("SPAWNDROID_INSTALL_MULTIPLE_APKS=NOT_RUN")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 0
    except (SplitError, json.JSONDecodeError, OSError) as exc:
        reason = str(exc) if isinstance(exc, SplitError) else "invalid_manifest_or_io"
        print("KWAI_SPLIT_GUARD=" + reason)
        print("SPAWNDROID_INSTALL_MULTIPLE_APKS=NOT_PROVEN")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25


if __name__ == "__main__":
    sys.exit(main())
