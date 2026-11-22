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
        if account == "universo.anthares":
            # Primary state is maintained in the authenticated browser vault.
            from tiktok_session_authority import load_canonical_state
            from cortes_tiktok_queue_consumer import qcall, oidc
            state, _ = load_canonical_state()
            token = oidc()
            def request(action, payload=None):
                return qcall(action, token, payload)
        else:
            from cortes_tiktok_lucasrosalem4_cloud_publish import (
                state_from_secret, call, oidc)
            state = state_from_secret()
            token = oidc()
            def request(action, payload=None):
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
