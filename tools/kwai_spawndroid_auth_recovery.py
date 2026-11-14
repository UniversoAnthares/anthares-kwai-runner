#!/usr/bin/env python3
"""Fail-closed recovery policy for disposable SpawnDroid Android sessions.

Agent 05 contract. Never logs in, reads credentials, restores app data,
allocates Android devices or publishes media. The authenticated Cloudflare
vault is preserved but is not an approved cross-container restore mechanism.
Appium evidence must originate in the trusted current-session controller.
"""
from __future__ import annotations

import json
import re
import sys
import time

ACCOUNT_PACKAGES = {
    "universoanthares": "com.kwai.video",
    "lucasrosalem": "kwai.lite.video",
}
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{8,130}$")
MAX_EVIDENCE_AGE_SECONDS = 120
MAX_FUTURE_SKEW_SECONDS = 5
FAILURE_STATES = {
    "otp_required": ("HUMAN_REQUIRED", "OWNER_VERIFICATION"),
    "mfa_required": ("HUMAN_REQUIRED", "OWNER_VERIFICATION"),
    "captcha_required": ("HUMAN_REQUIRED", "OWNER_VERIFICATION"),
    "device_approval_required": ("HUMAN_REQUIRED", "OWNER_VERIFICATION"),
    "auth_expired": ("REAUTH_REQUIRED", "OFFICIAL_LOGIN"),
    "auth_revoked": ("REAUTH_REQUIRED", "OFFICIAL_LOGIN"),
    "unauthorized": ("REAUTH_REQUIRED", "OFFICIAL_LOGIN"),
    "session_not_found": ("SESSION_TERMINAL", "CHECK_PROVIDER_TERMINAL"),
    "security_denied": ("SECURITY_BLOCKED", "OWNER_OR_PROVIDER_REVIEW"),
    "quota_exhausted": ("QUOTA_CANCEL_REQUIRED", "CANCEL_AND_CONFIRM_TERMINAL"),
    "concurrency_limit": ("RUNNER_SLOT_BUSY", "RECONCILE_EXISTING_RUNNER"),
    "host_unavailable": ("PROVIDER_UNAVAILABLE", "SAFE_STOP"),
    "transport_timeout": ("SESSION_UNCERTAIN", "READ_PROVIDER_BEFORE_RETRY"),
}
ERROR_ALIASES = {
    "401": "unauthorized", "403": "security_denied",
    "402": "quota_exhausted", "429": "concurrency_limit",
    "502": "host_unavailable", "503": "host_unavailable",
}
PUBLISH_IN_FLIGHT = frozenset({
    "started", "uncertain", "cancel_unconfirmed", "reconcile_required"
})


def _decision(status, action, *, current_identity=False,
              composer_access=False, reason=""):
    """Return fixed, safe codes. Never reflect caller-supplied strings."""
    return {
        "status": status,
        "action": action,
        "identity_verified_current_session": bool(current_identity),
        "publisher_ui_verified_current_session": bool(composer_access),
        "publication_authorized": False,
        "cloud_cutover_authorized": False,
        "automatic_retry_allowed": False,
        "reason_code": reason or status,
    }


def decide(request, *, now_epoch=None):
    """Assess one Android session. No authentication from previous sessions.

    The caller MUST directly collect Appium UI evidence for this exact session
    and independently verify the authoritative Neon ledger. This pure policy
    is not a cryptographic attestation of untrusted JSON. A positive decision
    permits only the separate, existing lease/CAS verification to proceed.
    """
    if not isinstance(request, dict):
        return _decision("BLOCKED", "FIX_CONTROLLER_INPUT")
    account = request.get("account")
    if not isinstance(account, str) or account not in ACCOUNT_PACKAGES:
        return _decision("BLOCKED", "FIX_CONTROLLER_ACCOUNT",
                         reason="ACCOUNT_INVALID")
    expected_package = ACCOUNT_PACKAGES[account]
    if request.get("package") != expected_package:
        return _decision("BLOCKED", "FIX_APP_PACKAGE",
                         reason="APP_ACCOUNT_PACKAGE_MISMATCH")
    session = request.get("session_id")
    if not isinstance(session, str) or not SESSION_RE.fullmatch(session):
        return _decision("BLOCKED", "CHECK_PROVIDER_SESSION",
                         reason="SESSION_ID_INVALID")

    # Reconcile prior started/uncertain uploads even after Android teardown.
    ledger = request.get("ledger_state")
    if not isinstance(ledger, str) or ledger.lower() not in {"idle", "settled"}:
        return _decision("RECONCILE_REQUIRED", "READ_CANONICAL_LEDGER")
    error = request.get("failure")
    if error:
        error = ERROR_ALIASES.get(str(error).lower(), str(error).lower())
        status, action = FAILURE_STATES.get(
            error, ("BLOCKED", "INSPECT_SANITIZED_FAILURE"))
        return _decision(status, action)
    if request.get("provider_session_state") != "ready":
        return _decision("SESSION_NOT_READY", "CHECK_PROVIDER_SESSION")

    observation = request.get("observation")
    if not isinstance(observation, dict):
        return _decision("AUTH_REQUIRED", "OFFICIAL_LOGIN_OR_OWNER_HANDOFF")
    if observation.get("challenge_required") is True:
        return _decision("HUMAN_REQUIRED", "OWNER_VERIFICATION")
    if observation.get("source") != "appium_live":
        return _decision("BLOCKED", "RECOLLECT_TRUSTED_EVIDENCE",
                         reason="EVIDENCE_SOURCE_INVALID")
    if observation.get("session_id") != session:
        return _decision("AUTH_REQUIRED", "RECOLLECT_CURRENT_SESSION",
                         reason="STALE_OR_CROSS_SESSION_PROOF")
    if observation.get("foreground_package") != expected_package:
        return _decision("BLOCKED", "CHECK_FOREGROUND_PACKAGE",
                         reason="FOREGROUND_APP_MISMATCH")

    timestamp = observation.get("observed_at_epoch")
    now = int(time.time()) if now_epoch is None else now_epoch
    if (type(now) is not int or type(timestamp) is not int
            or timestamp > now + MAX_FUTURE_SKEW_SECONDS
            or now - timestamp > MAX_EVIDENCE_AGE_SECONDS):
        return _decision("REAUTH_REQUIRED", "RECOLLECT_FRESH_APP_UI",
                         reason="EVIDENCE_STALE")
    observed_handle = observation.get("profile_handle")
    if (not isinstance(observed_handle, str)
            or observed_handle.lower().removeprefix("@") != account
            or observation.get("owner_edit_control") is not True):
        return _decision("AUTH_REQUIRED", "OFFICIAL_LOGIN_OR_OWNER_HANDOFF",
                         reason="EXACT_OWNER_IDENTITY_UNVERIFIED")
    if observation.get("publisher_entry_visible") is not True:
        return _decision("AUTHENTICATED_UI_PENDING", "VERIFY_UPLOAD_UI",
                         current_identity=True)
    return _decision("AUTHENTICATED_CURRENT_SESSION",
                     "CONTINUE_TO_SEPARATE_LEASE_CAS_GATE",
                     current_identity=True, composer_access=True)


def main():
    # Do not log/store input: unknown fields might contain private data.
    try:
        result = decide(json.load(sys.stdin))
    except (ValueError, UnicodeError, TypeError):
        result = _decision("BLOCKED", "FIX_CONTROLLER_INPUT")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "AUTHENTICATED_CURRENT_SESSION" else 2


if __name__ == "__main__":
    sys.exit(main())
