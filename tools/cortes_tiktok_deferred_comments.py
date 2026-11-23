#!/usr/bin/env python3
"""Five daily independent TikTok comment windows; publishing never waits for them.

Both accounts reuse their canonical authenticated browser state. A challenge,
missing composer, busy/unavailable runtime or zero eligible videos leaves the
confirmed clip unattempted in Neon for another window. The Neon uniqueness
fence remains authoritative: at most one actual attempt per published video.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Callable

# The canonical primary session authority lives outside tools/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'direct-tiktok-publisher'))

from cortes_tiktok_after_publish_comment import after_confirmed

ACCOUNTS = ("universo.anthares", "lucasrosalem4")
STOP_RESULTS = frozenset({"security_challenge", "unavailable", "no_target",
                          "session_unavailable", "history_unavailable",
                          "composer_unavailable"})
MAX_PER_WINDOW = 5

# Independent, namespaced recovery ledger on the existing free Neon project.
# This path is strictly comments-only; no upload or publisher action is exposed.
# Before returning to the legacy ledger, reconcile receipts made here.
COMMENT_RECOVERY_ENDPOINTS = {
    "universo.anthares": "https://br-dark-rice-b7jf2e9e-cortescmtmain.compute.c-13.us-east-1.aws.neon.tech/",
    "lucasrosalem4": "https://br-dark-rice-b7jf2e9e-cortescmtlucas.compute.c-13.us-east-1.aws.neon.tech/",
}
COMMENT_ACTIONS = frozenset({"comment-pending", "comment-recent",
                             "comment-reserve", "comment-complete"})


def recovery_request(account: str, token: str, action: str, payload=None) -> dict:
    """Signed GitHub OIDC, canonical host and comment-only verbs; fail closed."""
    import json
    import urllib.request
    import urllib.error
    if account not in COMMENT_RECOVERY_ENDPOINTS or action not in COMMENT_ACTIONS:
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_ROUTE_REJECTED")
    if not isinstance(token, str) or len(token) < 200:
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_AUTH_MISSING")
    if payload is not None and action not in ("comment-reserve", "comment-complete"):
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_METHOD_INVALID")
    if payload is None and action in ("comment-reserve", "comment-complete"):
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_METHOD_INVALID")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else None
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        COMMENT_RECOVERY_ENDPOINTS[account] + "?action=" + action,
        data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            if response.status != 200:
                raise RuntimeError("TIKTOK_COMMENT_RECOVERY_HTTP_NON200")
            data = json.loads(response.read(65536))
    except urllib.error.HTTPError as exc:
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_HTTP_" + str(exc.code)) from None
    except urllib.error.URLError:
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_TRANSPORT_UNAVAILABLE") from None
    if not isinstance(data, dict) or data.get("ok") is not True:
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_RESPONSE_DENIED")
    if action in ("comment-pending", "comment-recent") and data.get("account") != account:
        raise RuntimeError("TIKTOK_COMMENT_RECOVERY_IDENTITY_MISMATCH")
    return data



def pending_ids(data: object, account: str) -> list[str]:
    """Only accept a known account, confirmed numeric IDs and bounded result."""
    if not isinstance(data, dict) or data.get("ok") is not True or data.get("account") != account:
        raise RuntimeError("TIKTOK_DEFERRED_PENDING_UNVERIFIED")
    items = data.get("pending")
    if not isinstance(items, list) or len(items) > MAX_PER_WINDOW:
        raise RuntimeError("TIKTOK_DEFERRED_PENDING_INVALID")
    unique: list[str] = []
    for row in items:
        if not isinstance(row, dict):
            raise RuntimeError("TIKTOK_DEFERRED_PENDING_INVALID")
        video_id = str(row.get("source_video_id") or "")
        if not video_id.isdecimal() or not 12 <= len(video_id) <= 25 or video_id in unique:
            raise RuntimeError("TIKTOK_DEFERRED_SOURCE_ID_INVALID")
        unique.append(video_id)
    return unique


def run_account(account: str, state: dict, request: Callable, *,
                play_runtime=None, action=after_confirmed) -> dict:
    """Read pending before starting a browser; stop when TikTok asks for verification."""
    source_ids = pending_ids(request("comment-pending"), account)
    print(f"TIKTOK_DEFERRED_PENDING account={account} count={len(source_ids)}", flush=True)
    if not source_ids:
        return {"account": account, "attempted": 0, "state": "idle"}
    if not isinstance(state, dict) or not isinstance(state.get("cookies"), list):
        raise RuntimeError("TIKTOK_DEFERRED_SESSION_INVALID")

    from playwright.sync_api import sync_playwright
    browser_context = play_runtime or sync_playwright()
    attempted = 0
    state_out = "complete"
    with browser_context as runtime:
        browser = runtime.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
        try:
            context = browser.new_context(
                storage_state=state, locale="pt-BR",
                viewport={"width": 1280, "height": 900})
            try:
                page = context.new_page()
                for source_id in source_ids:
                    # This code path is the only one permitted to reserve comments.
                    outcome = action(
                        account=account, source_video_id=source_id, existing_page=page,
                        recent_call=lambda: request("comment-recent"),
                        reserve_call=lambda payload: request("comment-reserve", payload),
                        complete_call=lambda payload: request("comment-complete", payload))
                    print(f"TIKTOK_DEFERRED_OUTCOME account={account} status={outcome}",
                          flush=True)
                    attempted += 1
                    if outcome in STOP_RESULTS:
                        state_out = outcome
                        break
            finally:
                context.close()
        finally:
            browser.close()
    return {"account": account, "attempted": attempted, "state": state_out}


def main() -> int:
    account = os.environ.get("TIKTOK_DEFERRED_ACCOUNT", "").strip().lstrip("@").lower()
    if account not in ACCOUNTS:
        print("TIKTOK_DEFERRED_ACCOUNT_NOT_ALLOWLISTED=1", flush=True)
        return 2
    try:
        use_recovery = os.getenv("TIKTOK_COMMENT_RECOVERY_ENABLED", "false").lower() == "true"
        if account == "universo.anthares":
            # Primary state is maintained in the authenticated browser vault.
            from tiktok_session_authority import load_canonical_state
            from cortes_tiktok_queue_consumer import qcall, oidc
            state, _ = load_canonical_state()
            token = oidc()
            def request(action, payload=None):
                if use_recovery:
                    return recovery_request(account, token, action, payload)
                return qcall(action, token, payload)
        else:
            from cortes_tiktok_lucasrosalem4_cloud_publish import (
                state_from_secret, call, oidc)
            state = state_from_secret()
            token = oidc()
            def request(action, payload=None):
                if use_recovery:
                    return recovery_request(account, token, action, payload)
                return call(action, token, payload)
        result = run_account(account, state, request)
        print("TIKTOK_DEFERRED_FINAL account=" + result["account"] +
              " state=" + result["state"] +
              " attempted=" + str(result["attempted"]), flush=True)
        return 0
    except Exception as exc:
        # Preserve privacy of cookies, auth headers, and account state.
        code = str(exc)
        if re.fullmatch(r"[A-Z][A-Z0-9_]{3,100}", code):
            print("TIKTOK_DEFERRED_HOLD=" + code, flush=True)
        else:
            print("TIKTOK_DEFERRED_HOLD=" + type(exc).__name__, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
