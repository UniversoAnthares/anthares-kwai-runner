#!/usr/bin/env python3
"""One-shot real Android install canary for ORIGINAL Kwai splits on SpawnDroid.

Cloud only. Requires GitHub-hosted workflow_dispatch, owner-approved device
quota, an authorized SpawnDroid API key, existing demo artifact, and 25 APKs
verified with the Google Android SDK on this ephemeral runner.

Never logs into Kwai, uploads videos, posts media, or changes cloud cutover.
No SpawnDroid API key -> no device or external OIDC call.
"""
from __future__ import annotations

import hmac
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import kwai_spawndroid_oidc_cloud_audit as source
import kwai_spawndroid_original_splits as splits

API = "https://app.spawndroid.io"
ARTIFACT = "spawndroid-demo-ae64feef92"
PACKAGE = "com.kwai.video"
VERSION = 647103
SIGNED_BYTES = 202108730
SESSION_RX = re.compile(r"^sess_[a-zA-Z0-9_-]{8,100}$")
WD_SESSION_RX = re.compile(r"^[a-zA-Z0-9_-]{8,130}$")
TERMINAL = frozenset(("terminated", "ended", "completed", "failed",
                      "stopped", "cancelled", "closed"))
STATE_WAIT_S = 115


class CanaryBlocked(Exception):
    """Only sanitized status identifiers are emitted to CI output."""


def required_gates(env: dict) -> tuple[str, str]:
    """Validate all permission, cost and identity gates before network IO."""
    required = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": source.REPO,
        "GITHUB_REF": source.BRANCH,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED": "1",
        "SPAWNDROID_HOBBY_FREE_CONFIRMED": "1",
    }
    for name, expected in required.items():
        if env.get(name) != expected:
            raise CanaryBlocked("gate_" + name.lower() + "_disabled")
    if not env.get("RUNNER_TEMP") or not Path(env["RUNNER_TEMP"]).is_dir():
        raise CanaryBlocked("github_runner_temp_required")
    key = env.get("SPAWNDROID_API_KEY", "").strip()
    if not key or len(key) < 16 or "\n" in key:
        raise CanaryBlocked("spawndroid_official_api_key_missing")
    slug = env.get("SPAWNDROID_DEMO_ARTIFACT_SLUG", "")
    if slug != ARTIFACT:
        raise CanaryBlocked("demo_artifact_identity_unverified")
    run_id = str(env.get("GITHUB_RUN_ID", "")).strip()
    attempt = str(env.get("GITHUB_RUN_ATTEMPT", "1")).strip()
    if not re.fullmatch(r"\d{5,25}", run_id) or not re.fullmatch(r"\d{1,3}", attempt):
        raise CanaryBlocked("github_idempotency_identity_missing")
    return key, "kwai-item1-" + run_id + "-" + attempt


def _request(method, url, token="", body=None, headers=None, *, timeout=24):
    """Client with strict host, sanitized errors, no automatic retries."""
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    if (parts.scheme != "https" or not host or
        host not in ("app.spawndroid.io", "stream.spawndroid.io") and
        not host.endswith(".spawndroid.io") or
        parts.username or parts.password):
        raise CanaryBlocked("remote_endpoint_not_allowlisted")
    hdr = {"Accept": "application/json"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    if headers:
        hdr.update(headers)
    data = json.dumps(body).encode("utf8") if body is not None else None
    if data is not None:
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, method=method, headers=hdr, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(500000)
        val = json.loads(raw)
        if not isinstance(val, dict):
            raise CanaryBlocked("remote_response_not_json_object")
        return val
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise CanaryBlocked("remote_auth_denied_" + str(exc.code)) from None
        if exc.code == 402:
            raise CanaryBlocked("hobby_device_minutes_exhausted") from None
        if exc.code == 429:
            raise CanaryBlocked("spawndroid_concurrency_slot_busy") from None
        if exc.code == 409:
            raise CanaryBlocked("session_start_in_progress_reconcile") from None
        raise CanaryBlocked("remote_http_" + str(exc.code)) from None
    except (OSError, ValueError):
        raise CanaryBlocked("remote_transport_uncertain_reconcile") from None


def preflight_workspace(key, request=_request):
    apps = request("GET", API + "/api/apps", key).get("apps")
    if not isinstance(apps, list):
        raise CanaryBlocked("workspace_apps_unreadable")
    match = [x for x in apps if isinstance(x, dict) and x.get("slug") == ARTIFACT]
    if len(match) != 1:
        raise CanaryBlocked("authorized_demo_artifact_missing")
    sessions = request("GET", API + "/api/sessions", key).get("sessions")
    if not isinstance(sessions, list):
        raise CanaryBlocked("workspace_sessions_unreadable")
    for session in sessions:
        if not isinstance(session, dict):
            raise CanaryBlocked("workspace_session_state_ambiguous")
        status = str(session.get("status") or session.get("state") or "").lower()
        ended = session.get("endedAt") or session.get("ended_at")
        if not ended and status not in TERMINAL:
            raise CanaryBlocked("workspace_has_live_or_unknown_session")
    return True


def verify_cloud_source(env):
    """Manifest is issued by Hostinger only after GitHub OIDC verification."""
    token = source._get_oidc()
    source._assert_claims_shape(token)
    doc = source._fetch_manifest(token)
    del token
    parsed = splits.validate_manifest(doc, {"anthares.us"})
    if (parsed["package"] != PACKAGE or parsed["versionCode"] != VERSION or
        len(parsed["files"]) != 25 or parsed["bytes"] != SIGNED_BYTES):
        raise CanaryBlocked("original_split_manifest_changed")
    expires = doc.get("expiresAt")
    if type(expires) is not int or not time.time() + 120 < expires <= time.time() + 1600:
        raise CanaryBlocked("cloud_source_urls_expired_or_invalid")
    return doc, parsed


def _webdriver_endpoint(endpoint):
    url = urllib.parse.urlsplit(str(endpoint))
    if (url.scheme != "https" or
        not (url.hostname or "").endswith(".spawndroid.io") or
        url.username or url.password or not url.path.startswith("/ci/") or
        not url.path.rstrip("/").endswith("/wd/hub")):
        raise CanaryBlocked("webdriver_endpoint_invalid")
    return str(endpoint).rstrip("/")


def _wd_session_id(response):
    v = response.get("value")
    if not isinstance(v, dict):
        raise CanaryBlocked("webdriver_create_invalid")
    s = v.get("sessionId") or response.get("sessionId")
    if not isinstance(s, str) or not WD_SESSION_RX.fullmatch(s):
        raise CanaryBlocked("webdriver_session_identifier_invalid")
    return s


def webdriver_executor(webdriver_url, wd_id, request=_request):
    def execute(script, arguments):
        path = webdriver_url + "/session/" + wd_id + "/execute/sync"
        data = request("POST", path, body={"script": script, "args": [arguments]},
                       timeout=195)
        if isinstance(data.get("value"), dict) and data["value"].get("error"):
            raise CanaryBlocked("webdriver_execute_error")
        return data.get("value")
    return execute


def _get_ready(session_id, key, request=_request, *, wait=STATE_WAIT_S, clock=time.monotonic,
               sleep=time.sleep):
    deadline = clock() + wait
    while clock() <= deadline:
        d = request("GET", API + "/api/v1/sessions/" + session_id, key)
        state = d.get("state")
        if state == "ready":
            return d
        if state in ("failed", "terminated", "ended", "stopped"):
            raise CanaryBlocked("android_device_failed_before_ready")
        if state not in ("booting", "provisioning", "starting", "pending", "queued"):
            raise CanaryBlocked("android_device_unknown_state")
        sleep(3)
    raise CanaryBlocked("android_device_boot_timeout")


def _close_session(session_id, key, *, passed, request=_request):
    r = request("DELETE", API + "/api/v1/sessions/" + session_id,
                key, body={"result": "passed" if passed else "failed"})
    if r.get("ok") is not True:
        raise CanaryBlocked("device_teardown_not_acknowledged")
    # Confirm provider state through independent readback.
    history = request("GET", API + "/api/sessions", key).get("sessions")
    if not isinstance(history, list):
        raise CanaryBlocked("device_teardown_readback_unavailable")
    found = [s for s in history if isinstance(s, dict) and
             str(s.get("id") or s.get("sessionId") or "") == session_id]
    if len(found) != 1:
        raise CanaryBlocked("device_teardown_readback_missing")
    row = found[0]
    state = str(row.get("status") or row.get("state") or "").lower()
    if not (row.get("endedAt") or row.get("ended_at") or state in TERMINAL):
        raise CanaryBlocked("device_teardown_not_confirmed")
    return True


def run_real_canary(env=os.environ, *, request=_request):
    key, idem = required_gates(env)
    # Read-only preflight even before OIDC network and ephemeral downloads.
    preflight_workspace(key, request=request)
    doc, parsed = verify_cloud_source(env)
    installed = False
    session_id = ""
    wd_id = ""
    wd_url = ""
    closed = False
    outcome = "CANARY_FAILED_UNVERIFIED"
    try:
        with tempfile.TemporaryDirectory(prefix="kwai-spawndroid-canary-",
                                         dir=env["RUNNER_TEMP"]) as tmp:
            receipt = splits.download_and_verify(parsed, {"anthares.us"}, Path(tmp))
            if (receipt.get("signed_splits_verified") is not True or
                receipt.get("count") != 25 or receipt.get("bytes") != SIGNED_BYTES or
                receipt.get("cert") != splits.guard.EXPECTED_CERT_SHA256):
                raise CanaryBlocked("original_splits_crypto_audit_failed")
            print("KWAI_SPLITS_CRYPTOGRAPHIC_AUDIT=PASS", flush=True)
            # Recheck slot after the potentially long binary verification.
            preflight_workspace(key, request=request)
            # Exactly ONE session creation with a deterministic key.
            created = request("POST", API + "/api/v1/sessions", key,
                              body={"artifactId": ARTIFACT,
                                    "profileId": "android-14-phone"},
                              headers={"Idempotency-Key": idem},
                              timeout=45)
            session_id = str(created.get("sessionId") or "")
            if not SESSION_RX.fullmatch(session_id):
                raise CanaryBlocked("session_id_missing_reconcile_manually")
            ready = _get_ready(session_id, key, request=request)
            serial = (ready.get("device") or {}).get("serial") or (
                (created.get("device") or {}).get("serial"))
            wd_url = _webdriver_endpoint(
                ready.get("webdriverUrl") or created.get("webdriverUrl"))
            caps = {
                "capabilities": {
                    "alwaysMatch": {
                        "platformName": "Android",
                        "appium:automationName": "UiAutomator2",
                    },
                    "firstMatch": [{}],
                },
            }
            if isinstance(serial, str) and serial:
                caps["capabilities"]["alwaysMatch"]["appium:udid"] = serial
            wd = request("POST", wd_url + "/session", body=caps, timeout=90)
            wd_id = _wd_session_id(wd)
            execute = webdriver_executor(wd_url, wd_id, request=request)
            urls = [entry["url"] for entry in parsed["files"]]
            evidence = splits.webdriver_script(
                execute, PACKAGE, VERSION, urls, manifest=doc,
                verified_directory=Path(tmp), approved_hosts={"anthares.us"},
            )
            if evidence.get("installed") is not True:
                raise CanaryBlocked("kwai_installed_receipt_missing")
            installed = True
            print("KWAI_ORIGINAL_SPLITS_REMOTE_INSTALLED=PASS", flush=True)
            # Launch only the app. No login, publishing, media or account work.
            execute("mobile: activateApp", {"appId": PACKAGE})
            foreground = execute("mobile: queryAppState", {"appId": PACKAGE})
            if foreground != 4:
                raise CanaryBlocked("kwai_foreground_not_verified")
            outcome = "KWAI_ORIGINAL_KWAI_FOREGROUND=PASS"
            return {"installed": True, "foreground": True,
                    "pkg": PACKAGE, "version": VERSION,
                    "published": False, "authenticated": False}
    finally:
        if wd_id and wd_url:
            try:
                request("DELETE", wd_url + "/session/" + wd_id, timeout=30)
            except CanaryBlocked:
                print("SPAWNDROID_WEBDRIVER_TEARDOWN=UNCERTAIN", flush=True)
        if session_id:
            try:
                closed = _close_session(session_id, key, passed=(
                    outcome == "KWAI_ORIGINAL_KWAI_FOREGROUND=PASS"), request=request)
                print("SPAWNDROID_DEVICE_TEARDOWN=" +
                      ("PASS" if closed else "UNCERTAIN"), flush=True)
            except CanaryBlocked:
                print("SPAWNDROID_DEVICE_TEARDOWN=RECONCILE_REQUIRED", flush=True)
                # A successful install may not be reported while its runner
                # remains possibly active; preserve a visible failed state.
                raise CanaryBlocked("device_teardown_reconcile_required") from None
        print("KWAI_PUBLICATION_ATTEMPTED=0", flush=True)


def main() -> int:
    try:
        receipt = run_real_canary()
        print("KWAI_ORIGINAL_KWAI_FOREGROUND=PASS")
        print("KWAI_INSTALL_ONLY=PASS")
        return 0
    except (CanaryBlocked, splits.SplitError) as exc:
        value = str(exc)
        if not re.fullmatch(r"[a-z0-9_.-]{4,130}", value):
            value = "safe_abort"
        print("KWAI_SPAWNDROID_CANARY=" + value)
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25
    except Exception:
        print("KWAI_SPAWNDROID_CANARY=unexpected_error_reconcile")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25


if __name__ == "__main__":
    sys.exit(main())
