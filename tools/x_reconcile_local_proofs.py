#!/usr/bin/env python3
"""Reconcile proven local Anthares Browser X posts into trusted GH Actions proofs.

Never submits a video or operates a browser. Cross-checks each local successful
issue comment against the authoritative Northflank PostgreSQL ledger before
marking the issue as a trusted github-actions[bot] video confirmation.
"""
import json
import os
import urllib.parse
import urllib.request

from tools.x_issue_publisher import fingerprint
from tools.x_publication_safety import _issue_payload, verified_post_url

REPO = "UniversoAnthares/anthares-kwai-runner"
ROOT = "https://api.github.com/repos/" + REPO
BASE = "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x"


def api(path, method="GET", body=None):
    token = os.environ["GH_TOKEN"]
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(ROOT + path, method=method, data=data, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "anthares-x-ledger-reconcile",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def ledger(key):
    shared = os.environ["ARA_SHARED"]
    url = BASE + "/post-status?idempotency_key=" + urllib.parse.quote(key, safe="")
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + shared,
        "User-Agent": "anthares-x-ledger-reconcile",
    })
    with urllib.request.urlopen(req, timeout=22) as resp:
        return json.load(resp)


def local_proof(comments):
    for comment in comments:
        if (comment.get("user") or {}).get("login") != "UniversoAnthares":
            continue
        body = comment.get("body") or ""
        if not body.startswith("X_LOCAL_VIDEO_CONFIRMED_V1"):
            continue
        try:
            obj = json.loads(body.split("\n", 1)[1])
        except (ValueError, IndexError):
            continue
        if (obj.get("kind") == "X_VIDEO_CONFIRMED_V1"
                and obj.get("account") == "lucasyahn"
                and obj.get("video_verified") is True
                and verified_post_url(str(obj.get("post_url") or "")) == obj.get("post_url")):
            return obj
    return None


def trusted_proof_present(comments):
    return any(
        (c.get("user") or {}).get("login") == "github-actions[bot]"
        and "X_VIDEO_CONFIRMED_V1" in str(c.get("body") or "")
        for c in comments
    )


def reconcile(issue, comments, readback):
    if issue.get("state") != "closed" or not str(issue.get("title") or "").startswith("[X-PUBLISH]"):
        return None
    payload = _issue_payload(issue.get("body"))
    if (payload.get("account") != "lucasyahn" or payload.get("platform") != "x"
            or payload.get("test_fixture")):
        return None
    if trusted_proof_present(comments):
        return None
    proof = local_proof(comments)
    if proof is None:
        return None
    key = fingerprint(payload)
    if proof.get("idempotency_key") != key:
        return None
    status = readback(key)
    if (status.get("ok") is not True or status.get("status") != "CONFIRMED"
            or status.get("post_url") != proof["post_url"]):
        return None
    return {
        "kind": "X_VIDEO_CONFIRMED_V1",
        "account": "lucasyahn",
        "video_verified": True,
        "post_url": proof["post_url"],
        "idempotency_key": key,
    }


def run():
    found = 0
    scanned = 0
    for page in range(1, 7):
        issues = api(f"/issues?state=closed&sort=updated&direction=desc&per_page=100&page={page}")
        for issue in issues:
            if issue.get("pull_request") or not str(issue.get("title") or "").startswith("[X-PUBLISH]"):
                continue
            if not issue.get("comments"):
                continue
            scanned += 1
            number = int(issue["number"])
            try:
                comments = api(f"/issues/{number}/comments?per_page=100")
                if len(comments) == 100:
                    continue
                proof = reconcile(issue, comments, ledger)
                if proof is None:
                    continue
                api(f"/issues/{number}/comments", "POST", {
                    "body": "X_VIDEO_CONFIRMED_V1\n" + json.dumps(proof, ensure_ascii=False, separators=(",", ":"))
                })
                print("X_LOCAL_PROOF_RECONCILED=" + str(number) + " URL=" + proof["post_url"], flush=True)
                found += 1
            except Exception as exc:
                print("X_LOCAL_PROOF_RECONCILE_FAILED=" + str(number)
                      + " TYPE=" + type(exc).__name__, flush=True)
        if len(issues) < 100:
            break
    print("X_RECONCILE_DONE posts=" + str(found) + " scanned=" + str(scanned), flush=True)


if __name__ == "__main__":
    run()
