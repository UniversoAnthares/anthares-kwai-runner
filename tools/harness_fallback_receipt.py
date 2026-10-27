"""OIDC receipt for one SHA-pinned, Neon-fenced Harness CI fallback.

The server authenticates the exact GitHub workflow and atomically acquires the
successor slot. This client has no database or provider secret; uncertain calls
must never be retried as a new job.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ENDPOINT = "https://anthares-ci-quota-controller.vercel.app/api/harness-fallback-verify"


def submit(phase: str, sha: str, execution: str):
    if phase not in ("start", "finish"):
        raise ValueError("INVALID_PHASE")
    import re
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("INVALID_SHA")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", execution):
        raise ValueError("INVALID_HARNESS_EXECUTION")
    url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    auth = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    url += ("&" if "?" in url else "?") + urllib.parse.urlencode(
        {"audience": "anthares-ci-quota-controller"})
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + auth})
    with urllib.request.urlopen(req, timeout=10) as response:
        identity = json.load(response)["value"]
    payload = json.dumps({"phase": phase, "source_sha": sha,
                          "harness_execution_id": execution}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=payload, method="POST", headers={
            "Authorization": "Bearer " + identity,
            "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as response:
        receipt = json.load(response)
    expected = ("FALLBACK_EXECUTION_AUTHORIZED" if phase == "start"
                else "FALLBACK_CONFIRMED")
    if receipt.get("code") != expected:
        raise RuntimeError("FENCED_RECEIPT_UNVERIFIED")
    print("HARNESS_FALLBACK_" + phase.upper() + "=VERIFIED")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("USAGE: start|finish sha execution")
    submit(*sys.argv[1:])
