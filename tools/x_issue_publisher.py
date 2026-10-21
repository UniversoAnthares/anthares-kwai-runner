#!/usr/bin/env python3
"""Cloud-only, fail-closed consumer of Anthares X publication issues.

Each irreversible attempt is durably marked on GitHub *before* the worker call.
A timeout or crashed runner leaves an uncertain job for reconciliation; a new
run must never blindly re-submit it. GitHub Actions concurrency serializes this
consumer, and an account/source/segment fingerprint prevents cross-issue replays.
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
from datetime import datetime
from zoneinfo import ZoneInfo

from tools.x_publication_safety import _issue_payload, confirmed_today, gate, verified_post_url

REPO = "UniversoAnthares/anthares-kwai-runner"
BASE = "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x"
TZ = ZoneInfo("America/Campo_Grande")
START_MARKER = "X_SUBMISSION_STARTED_V1"
LEGACY_START_MARKER = "X_POST_SUBMISSION_STARTED_V1"
PROOF_MARKER = "X_VIDEO_CONFIRMED_V1"
UNCERTAIN_MARKER = "X_SUBMISSION_UNCERTAIN_V1"
ALLOWED_HOSTS = {"anthares.us", "www.anthares.us", "raw.githubusercontent.com", "github.com"}


def github(path, method="GET", body=None):
    token = os.environ["GH_TOKEN"]
    url = "https://api.github.com/repos/" + REPO + "/" + path.lstrip("/")
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, method=method, data=data, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "anthares-x-durable-issue-consumer",
    })
    with urllib.request.urlopen(request, timeout=35) as r:
        return json.load(r)


def paginate(path, max_pages=10):
    out = []
    for page in range(1, max_pages + 1):
        join = "&" if "?" in path else "?"
        rows = github(path + join + "per_page=100&page=" + str(page))
        if not isinstance(rows, list):
            raise RuntimeError("X_GITHUB_PAGE_INVALID")
        out.extend(rows)
        if len(rows) < 100:
            return out
    raise RuntimeError("X_GITHUB_PAGINATION_INCOMPLETE")


def comments(number):
    return paginate("issues/" + str(number) + "/comments", max_pages=3)


def issue_comment(number, body):
    return github("issues/" + str(number) + "/comments", "POST", {"body": body})


def fingerprint(payload):
    source = str(payload.get("source_id") or "").strip()
    start, end = payload.get("segment_start"), payload.get("segment_end")
    if not source or start is None or end is None:
        raise ValueError("X_SEGMENT_IDENTITY_REQUIRED")
    start, end = float(start), float(end)
    scan = float(payload.get("scan_start") or 0)
    if start < 0 or scan < 0 or end - start < 300 or end - start > 840:
        raise ValueError("X_SEGMENT_DURATION_INVALID")
    raw = "x|lucasyahn|" + source + "|" + format(start + scan, ".3f") + "|" + format(end + scan, ".3f")
    return hashlib.sha256(raw.encode()).hexdigest()


def eligible(issue):
    if issue.get("state") != "open" or not str(issue.get("title") or "").startswith("[X-PUBLISH]"):
        return None
    obj = _issue_payload(issue.get("body"))
    if (obj.get("platform") != "x" or obj.get("account") != "lucasyahn"
            or obj.get("duration_class") != "long" or obj.get("test_fixture")):
        return None
    try:
        duration = float((obj.get("microedit") or {}).get("final_duration"))
        if not 300 <= duration <= 840:
            return None
        media = urllib.parse.urlparse(str(obj.get("media_url") or ""))
        if (media.scheme != "https" or media.hostname not in ALLOWED_HOSTS
                or media.username or media.password or media.port not in (None,443)):
            return None
        caption = str(obj.get("caption") or "").strip()
        if not caption or len(caption) > 280:
            return None
        fingerprint(obj)
    except (ValueError, TypeError):
        return None
    return obj


def markers(rows):
    return [
        c.get("body", "") for c in rows
        if (c.get("user") or {}).get("login") == "github-actions[bot]"
        and any(m in str(c.get("body", "")) for m in (START_MARKER, LEGACY_START_MARKER, PROOF_MARKER, UNCERTAIN_MARKER))
    ]


def remote(path, method="GET", payload=None, timeout=110):
    auth = os.environ["ARA_SHARED"]
    if not auth:
        raise RuntimeError("X_REMOTE_AUTH_UNAVAILABLE")
    req = urllib.request.Request(BASE + path, method=method, headers={
        "Authorization": "Bearer " + auth,
        "Content-Type": "application/json",
        "User-Agent": "anthares-x-durable-consumer",
    }, data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as exc:
        # Avoid leaking potentially sensitive server response into CI logs.
        return exc.code, {}


def qa_alert(kind, detail):
    """Deduplicate one active P0 issue; never fail the caller on an alert outage."""
    title = "[QA-P0][X] durable publication blocker"
    try:
        open_issues = paginate("issues?state=open&sort=updated&direction=desc", max_pages=8)
        current = next((x for x in open_issues if x.get("title") == title), None)
        msg = "X_BLOCKER=" + str(kind)[:90] + "\n" + str(detail)[:900]
        if current:
            issue_comment(current["number"], msg)
        else:
            github("issues", "POST", {"title": title, "body": msg})
    except Exception:
        print("X_QA_ALERT_UNAVAILABLE", flush=True)


def run():
    if not (os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"):
        raise RuntimeError("X_CONSUMER_CLOUD_ONLY")
    if os.getenv("X_PUBLISH_ARM") != "1":
        print("X_PUBLISH_DISARMED", flush=True)
        return
    if not os.getenv("ARA_SHARED") or not os.getenv("GH_TOKEN"):
        raise RuntimeError("X_PUBLISH_CREDENTIALS_MISSING")
    now = datetime.now(TZ)
    all_issues = paginate("issues?state=all&sort=updated&direction=desc")
    all_comments = {}
    candidates = []
    seen_fingerprints = set()
    for item in all_issues:
        if item.get("pull_request"):
            continue
        p = _issue_payload(item.get("body"))
        if str(item.get("title") or "").startswith("[X-PUBLISH]"):
            n = item["number"]
            if item.get("comments"):
                all_comments[n] = comments(n)
            try:
                identity = fingerprint(p)
            except (ValueError, TypeError):
                identity = None
            if identity and any(
                    (START_MARKER in str(x.get("body") or "")
                     or LEGACY_START_MARKER in str(x.get("body") or ""))
                    and (x.get("user") or {}).get("login") == "github-actions[bot]"
                    for x in all_comments.get(n, [])):
                seen_fingerprints.add(identity)
                # Read-only reconciliation can recover an acknowledged X post
                # after the runner or GitHub comment operation failed.
                if not any(PROOF_MARKER in str(c.get("body") or "")
                           for c in all_comments.get(n, [])):
                    try:
                        _, result = remote("/post-status?idempotency_key=" +
                                          urllib.parse.quote("x_" + identity), timeout=35)
                        url = verified_post_url(str(result.get("post_url") or ""))
                        if result.get("status") == "CONFIRMED" and url:
                            proof = {"kind": PROOF_MARKER, "source_fingerprint": identity,
                                     "post_url": url, "account": "lucasyahn",
                                     "video_verified": True, "confirmed_at": datetime.now(TZ).isoformat()}
                            issue_comment(n, "CONFIRMED video\n" + json.dumps(proof, ensure_ascii=False))
                            github("issues/" + str(n), "PATCH", {"state": "closed"})
                            all_comments[n].append({
                                "body": "CONFIRMED video\n" + json.dumps(proof),
                                "user": {"login": "github-actions[bot]"},
                                "created_at": datetime.now(TZ).isoformat(),
                            })
                            item["state"] = "closed"
                            print("X_RECONCILED_EXISTING_POST=" + url, flush=True)
                    except Exception as exc:
                        print("X_RECONCILIATION_RETRY_LATER=" + type(exc).__name__, flush=True)
            if eligible(item) and not markers(all_comments.get(n, [])):
                candidates.append((item, p, identity))
    status = gate(all_issues, all_comments, now, target=10)
    print("X_CLOUD_CONSUMER_GATE=" + json.dumps({
        "confirmed": status["confirmed"], "inflight": status["inflight"],
        "due": status["due"], "candidates": len(candidates)}), flush=True)
    # Reserve a daily budget before any irreversible request.
    if status["confirmed"] >= 10:
        return
    candidates.sort(key=lambda x: (x[0].get("created_at") or "", x[0]["number"]))
    for issue, payload, fp in candidates:
        number = issue["number"]
        if not fp or fp in seen_fingerprints:
            print("X_DUPLICATE_SOURCE_SEGMENT_SKIPPED=" + str(number), flush=True)
            continue
        # Current-day queue only. Yesterday's items enter the manually
        # reconcilable reserve queue instead of being silently posted today.
        try:
            posted_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")).astimezone(TZ)
        except (ValueError, KeyError):
            continue
        if posted_at.date() != now.date():
            continue
        status_code, identity = remote("/verify", timeout=90)
        if status_code != 200 or identity.get("ok") is not True or identity.get("handle") != "lucasyahn":
            qa_alert("X_IDENTITY_UNAVAILABLE", "Preflight rejected; issue #" + str(number))
            raise RuntimeError("X_AUTH_PRECHECK_FAILED")
        # Durable audit record precedes the external publish operation.
        issue_comment(number, START_MARKER + "\nfingerprint=" + fp)
        try:
            status_code, result = remote("/post", method="POST", timeout=240, payload={
                "text": payload["caption"],
                "media_url": payload["media_url"],
                "idempotency_key": "x_" + fp,
            })
            proof_url = verified_post_url(str(result.get("post_url") or ""))
            if not (status_code == 200 and result.get("ok") is True
                    and result.get("video_verified") is True
                    and result.get("handle") == "lucasyahn" and proof_url):
                raise RuntimeError("X_REMOTE_POST_UNCONFIRMED")
            proof = {"kind": PROOF_MARKER, "source_fingerprint": fp,
                     "post_url": proof_url, "account": "lucasyahn",
                     "video_verified": True, "confirmed_at": datetime.now(TZ).isoformat()}
            issue_comment(number, "CONFIRMED video\n" + json.dumps(proof, ensure_ascii=False))
            github("issues/" + str(number), "PATCH", {"state": "closed"})
            print("X_VIDEO_CONFIRMED_URL=" + proof_url, flush=True)
            return
        except Exception as exc:
            try:
                issue_comment(number, UNCERTAIN_MARKER + "\n" + type(exc).__name__)
            finally:
                qa_alert("X_PUBLISH_UNCERTAIN", "Issue #" + str(number) + " requires readback; automatic retry blocked")
            raise RuntimeError("X_SUBMISSION_UNCERTAIN_NO_RETRY") from None
    print("X_CONSUMER_IDLE_NO_ELIGIBLE_JOB", flush=True)


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        print("X_CONSUMER_FAILED=" + type(error).__name__, flush=True)
        sys.exit(2)
