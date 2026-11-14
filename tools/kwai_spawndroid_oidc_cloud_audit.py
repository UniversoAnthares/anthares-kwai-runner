#!/usr/bin/env python3
"""Cloud-only audit of original Kwai split APKs behind Hostinger HMAC links.

Obtains a short-lived GitHub Actions OIDC JWT (never printed or saved),
sends it to a strict issuer/audience/repository/workflow-bound PHP broker,
downloads 25 original-signed APK splits into ephemeral $RUNNER_TEMP,
verifies each complete SHA256 and APK v2/v3 signature with Android apksigner,
checks package/version via aapt, then deletes the temporary directory.
No device, Appium session, login, or publication is initiated.
"""
from __future__ import annotations

import json
import base64
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import urllib.error

from kwai_spawndroid_original_splits import (
    SplitError, validate_manifest, download_and_verify
)

REPO = "UniversoAnthares/anthares-kwai-runner"
BRANCH = "refs/heads/feature/spawndroid-kwai-apk-verified-upload-20261114"
AUD = "urn:anthares:kwai:apk-stage:v1"
URL = "https://anthares.us/.well-known/anthares-kwai-apks/oidc-broker.php"
EXPECTED_COUNT = 25
EXPECTED_BYTES = 202108730


def _get_oidc() -> str:
    base = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not base.startswith("https://") or not request_token or "\n" in request_token:
        raise SplitError("github_oidc_not_available")
    url = base + ("&" if "?" in base else "?") + urllib.parse.urlencode({"audience": AUD})
    try:
        r = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + request_token,
            "Accept": "application/json",
        })
        with urllib.request.urlopen(r, timeout=20) as resp:
            data = json.loads(resp.read(20000))
        token = data.get("value")
        if not isinstance(token, str) or len(token) < 100 or len(token) > 16000:
            raise SplitError("github_oidc_invalid")
        return token
    except (ValueError, OSError):
        raise SplitError("github_oidc_request_failed") from None


def _assert_claims_shape(token: str) -> None:
    """Local diagnostics only; Hostinger MUST still cryptographically verify JWT."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("parts")
        encoded = parts[1]
        raw = base64.urlsafe_b64decode(encoded + "=" * ((-len(encoded)) % 4))
        claims = json.loads(raw)
        if not isinstance(claims, dict):
            raise ValueError("claims")
    except (ValueError, TypeError):
        raise SplitError("oidc_claims_unreadable") from None
    ref = BRANCH
    expected = {
        "iss": "https://token.actions.githubusercontent.com",
        "aud": AUD,
        "sub": "repo:" + REPO + ":ref:" + ref,
        "repository": REPO,
        "ref": ref,
        "ref_type": "branch",
        "event_name": "push",
        "runner_environment": "github-hosted",
        "workflow_ref": REPO + "/.github/workflows/kwai-spawndroid-stage-cloud-audit.yml@" + ref,
    }
    for key, value in expected.items():
        if claims.get(key) != value:
            # Only the static claim NAME is exposed; never JWT or value.
            raise SplitError("oidc_claim_" + key + "_mismatch")


def _fetch_manifest(token: str) -> dict:
    if not token:
        raise SplitError("github_oidc_missing")
    req = urllib.request.Request(
        URL, method="POST", data=b"{}",
        headers={
            "X-Github-Oidc-Token": token, "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise SplitError("broker_unauthorized_or_unavailable")
            doc = json.loads(resp.read(40000))
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code <= 599:
            raise SplitError("broker_http_" + str(exc.code)) from None
        raise SplitError("broker_response_invalid") from None
    except (ValueError, OSError):
        raise SplitError("broker_transport_or_json_unavailable") from None
    if not isinstance(doc, dict):
        raise SplitError("broker_payload_invalid")
    return doc


def audit_cloud() -> dict:
    if (os.environ.get("GITHUB_ACTIONS") != "true" or
        os.environ.get("GITHUB_REPOSITORY") != REPO or
        os.environ.get("GITHUB_REF") != BRANCH or
        os.environ.get("GITHUB_EVENT_NAME") != "push" or
        not os.environ.get("RUNNER_TEMP")):
        raise SplitError("github_hosted_push_precondition_failed")
    expiry_allow = 1600
    # Never log the OIDC JWT or any HMAC-signed APK URL.
    token = _get_oidc()
    _assert_claims_shape(token)
    doc = _fetch_manifest(token)
    del token
    source = validate_manifest(doc, {"anthares.us"})
    if (source["package"] != "com.kwai.video" or
        source["versionCode"] != 647103 or
        len(source["files"]) != EXPECTED_COUNT or
        source["bytes"] != EXPECTED_BYTES):
        raise SplitError("source_manifest_package_or_version_changed")
    import time
    expiration = doc.get("expiresAt")
    if (type(expiration) is not int or
        not time.time() + 60 < expiration <= time.time() + expiry_allow):
        raise SplitError("source_manifest_expiry_invalid")
    # Immutable private originals + 25 HMAC URLs. The public serving route
    # uses realpath and signed expiry checks. All filenames end in .apk.
    with tempfile.TemporaryDirectory(prefix="kwai-apk-audit-",
                                     dir=os.environ["RUNNER_TEMP"]) as directory:
        result = download_and_verify(source, {"anthares.us"}, Path(directory))
        if not result["signed_splits_verified"]:
            raise SplitError("cloud_signature_proof_missing")
        if result["count"] != EXPECTED_COUNT or result["bytes"] != EXPECTED_BYTES:
            raise SplitError("cloud_signature_proof_count_invalid")
        return {
            "package": result["package"],
            "count": result["count"],
            "bytes": result["bytes"],
            "signer_cert_sha256": result["cert"],
            "original_apks_signed": True,
        }


def main() -> int:
    try:
        result = audit_cloud()
        print("KWAI_CLOUD_ORIGINAL_25_APKS_SHA256_AND_APKSIGNER=PASS")
        print("KWAI_CLOUD_SOURCE_PACKAGE=" + result["package"])
        print("KWAI_CLOUD_SOURCE_COUNT=" + str(result["count"]))
        print("KWAI_CLOUD_SOURCE_TOTAL_BYTES=" + str(result["bytes"]))
        print("KWAI_CLOUD_SIGNER_CERT_SHA256=" + result["signer_cert_sha256"])
        print("SPAWNDROID_APK_UPLOAD=NOT_ATTEMPTED")
        print("SPAWNDROID_ANDROID_SESSION=NOT_ATTEMPTED")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 0
    except SplitError as exc:
        # Emit only developer-authored invariant identifiers. Never expose
        # urllib errors or signed URLs in logs.
        code = str(exc)
        if not re.fullmatch(r"[a-z0-9_]{4,100}", code):
            code = "cloud_apk_audit_failed"
        print("KWAI_CLOUD_ORIGINAL_APK_AUDIT=" + code)
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25
    except Exception:
        print("KWAI_CLOUD_ORIGINAL_APK_AUDIT=internal_failure")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25


if __name__ == "__main__":
    sys.exit(main())
