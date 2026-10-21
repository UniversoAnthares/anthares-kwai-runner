#!/usr/bin/env python3
"""Cloud-only single-item X issue consumer: durable BEGIN, no blind repost.

Input queue lives in GitHub issues. A publication is counted only after
a video-bearing X post URL is returned by the authenticated browser worker.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
WORKER = os.getenv(
    "X_CLOUD_WORKER_URL",
    "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x",
).rstrip("/")
REPO = os.getenv("GITHUB_REPOSITORY", "UniversoAnthares/anthares-kwai-runner")


def _json(url, *, method="GET", payload=None, headers=None, timeout=35):
    data = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
    h = {"Accept": "application/vnd.github+json", "User-Agent": "Anthares-X-Cloud-Consumer/1"}
    h.update(headers or {})
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def _github(url, *, method="GET", payload=None):
    token = os.environ["GH_TOKEN"]
    return _json(API + "/repos/" + REPO + url, method=method, payload=payload,
                 headers={"Authorization": "Bearer " + token})


def _worker(path, *, method="GET", payload=None, timeout=40):
    token = os.environ["X_WORKER_CLIENT_TOKEN"]
    return _json(WORKER + path, method=method, payload=payload,
                 headers={"Authorization": "Bearer " + token}, timeout=timeout)


def _payload(issue):
    from tools.x_publication_safety import _issue_payload
    return _issue_payload(issue.get("body"))


def _idempotency(body):
    identity = "|".join(str(body.get(k) or "") for k in (
        "account", "source_id", "segment_start", "segment_end", "media_url"))
    return "x-long-v1-" + hashlib.sha256(identity.encode()).hexdigest()[:48]


def _comments(issue_number):
    rows = _github(f"/issues/{issue_number}/comments?per_page=100")
    if len(rows) == 100:
        raise RuntimeError("X_ISSUE_COMMENTS_PAGINATION_REQUIRED")
    return rows


def _sent_marker(comments):
    return any("X_POST_SUBMISSION_STARTED_V1" in str(c.get("body") or "") for c in comments)


def _verified(url):
    from tools.x_publication_safety import verified_post_url
    return verified_post_url(url) == url


def _complete(issue, payload, info):
    url = str(info.get("post_url") or "")
    if not (info.get("ok") is True and info.get("video_verified") is True
            and str(info.get("handle") or "").lstrip("@").casefold() == "lucasyahn"
            and _verified(url)):
        raise RuntimeError("X_POST_CONFIRMATION_EVIDENCE_INVALID")
    # The confirming comment must be durable BEFORE closing the issue.
    _github(f"/issues/{issue['number']}/comments", method="POST", payload={
        "body": "CONFIRMED\n\nVideo verified on X, account @lucasyahn.\n"
                "Post: " + url + "\n"
                "X_VERIFIED_LONGFORM_V1\n"
                "Idempotency: " + _idempotency(payload)
    })
    _github(f"/issues/{issue['number']}", method="PATCH", payload={"state": "closed"})
    return url


def _list_open_x():
    result = []
    for page in range(1, 7):
        batch = _github(f"/issues?state=open&per_page=100&sort=created&direction=asc&page={page}")
        result.extend(i for i in batch if not i.get("pull_request") and
                      str(i.get("title") or "").startswith("[X-PUBLISH]"))
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("X_PUBLISH_ISSUE_PAGE_LIMIT")
    return result


def _process(issue):
    body = _payload(issue)
    if (body.get("platform") != "x" or body.get("account") != "lucasyahn"
            or body.get("test_fixture") or body.get("duration_class") != "long"):
        return "SKIP_UNQUALIFIED_ISSUE"
    media = str(body.get("media_url") or "")
    p = urllib.parse.urlparse(media)
    if p.scheme != "https" or p.hostname not in {
        "anthares.us", "www.anthares.us", "github.com", "raw.githubusercontent.com"
    } or p.username or p.password:
        return "SKIP_UNSAFE_MEDIA_URL"
    caption = str(body.get("caption") or "").strip()
    if not caption or len(caption) > 280:
        return "SKIP_INVALID_CAPTION"
    number = int(issue["number"])
    comments = _comments(number)
    key = _idempotency(body)

    if _sent_marker(comments):
        # Read-only reconciliation for a result lost after the last POST.
        try:
            status = _worker("/post-status?idempotency_key=" + urllib.parse.quote(key))
            if status.get("status") == "CONFIRMED" and _verified(str(status.get("post_url") or "")):
                url = _complete(issue, body, {"ok": True, "handle": "lucasyahn",
                                               "video_verified": True, "post_url": status["post_url"]})
                return "RECOVERED_CONFIRMED " + url
        except Exception as exc:
            print("X_RECONCILE_PROBE_FAILED=" + type(exc).__name__, flush=True)
        return "UNCERTAIN_PREEXISTING_RECONCILE"

    # Read-only preflight BEFORE writing irrevocable BEGIN evidence.
    verify = _worker("/verify", timeout=60)
    if not (verify.get("ok") is True and verify.get("handle") == "lucasyahn"
            and verify.get("durable") is True):
        raise RuntimeError("X_CLOUD_ACCOUNT_OR_VAULT_NOT_READY")
    _github(f"/issues/{number}/comments", method="POST", payload={
        "body": "X_POST_SUBMISSION_STARTED_V1\n"
                "idempotency_key=" + key + "\n"
                "Publisher: cloud browser; irreversible call may have occurred.\n"
                "Recovery: read-back first, never blind retry."
    })
    try:
        result = _worker("/post", method="POST",
                         payload={"text": caption, "media_url": media,
                                  "idempotency_key": key}, timeout=600)
    except Exception as exc:
        print("X_QA_P0_UNCERTAIN_POST issue=" + str(number)
              + " error=" + type(exc).__name__, flush=True)
        # BEGIN remains as durable fence. Never send a second POST.
        return "UNCERTAIN_NEW_SUBMISSION"
    return "CONFIRMED " + _complete(issue, body, result)


def main():
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.getenv("RUNNER_OS") != "Linux"):
        raise RuntimeError("X_CLOUD_ONLY_GUARD")
    if not os.getenv("GH_TOKEN") or not os.getenv("X_WORKER_CLIENT_TOKEN"):
        raise RuntimeError("X_CLOUD_CREDENTIAL_MISSING")
    uncertain = []
    for issue in _list_open_x():
        try:
            result = _process(issue)
        except Exception as exc:
            print("X_QA_P0_ITEM_BLOCKED issue=" + str(issue["number"])
                  + " error=" + type(exc).__name__, flush=True)
            uncertain.append(issue["number"])
            break
        if result in {"SKIP_UNQUALIFIED_ISSUE", "SKIP_UNSAFE_MEDIA_URL", "SKIP_INVALID_CAPTION"}:
            continue
        print(json.dumps({"issue": issue["number"], "status": result}), flush=True)
        if result.startswith(("CONFIRMED", "RECOVERED_CONFIRMED")):
            return 0
        uncertain.append(issue["number"])
        # A previous uncertain item must never prevent a distinct X clip from proceeding.
        # A newly attempted publish ends this invocation even on uncertain outcome.
        if result != "UNCERTAIN_PREEXISTING_RECONCILE":
            break
    if uncertain:
        print("X_QA_P0_UNCERTAIN_ISSUES=" + ",".join(map(str, uncertain)), flush=True)
        return 3
    print('{"status":"IDLE_NO_ELIGIBLE_X_ISSUES"}', flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"x_cloud_consumer": "BLOCKED",
                          "reason": type(exc).__name__}), flush=True)
        sys.exit(4)
