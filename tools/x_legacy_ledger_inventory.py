"""Read-only X idempotency inventory for cross-database migration.

Queries each historical X issue and authenticated old ledger. Never writes or
publishes and never includes credentials in stdout or exceptions.
"""
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request

REPO = "UniversoAnthares/anthares-kwai-runner"
ROOT = "https://api.github.com/repos/" + REPO
LEDGER = "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x"


def load(url, token):
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "Anthares-X-Ledger-Inventory",
    }
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=28) as res:
        if res.status != 200:
            raise RuntimeError("X_READBACK_HTTP_FAILURE")
        return json.load(res)


def fingerprint(data):
    source = str(data.get("source_id") or "").strip()
    start = float(data["segment_start"]) + float(data.get("scan_start") or 0)
    end = float(data["segment_end"]) + float(data.get("scan_start") or 0)
    if not source or start < 0 or end - start < 300 or end - start > 840:
        raise RuntimeError("X_INVALID_SOURCE_DURATION")
    raw = "x|lucasyahn|" + source + "|" + format(start, ".3f") + "|" + format(end, ".3f")
    return hashlib.sha256(raw.encode()).hexdigest()


def parsed(body):
    match = re.search(r"```json\s*(\{.*?\})\s*```", body or "", re.S)
    if not match:
        raise RuntimeError("X_ISSUE_BODY_INVALID")
    return json.loads(match.group(1))


def main():
    gh = os.getenv("GH_TOKEN", "")
    secret = os.getenv("ARA_SHARED", "")
    if not gh or not secret:
        raise RuntimeError("X_LEDGER_PROOF_SECRET_MISSING")
    query = urllib.parse.urlencode({"q": "repo:" + REPO + " in:title X-PUBLISH", "per_page": "100"})
    data = load("https://api.github.com/search/issues?" + query, gh)
    if data.get("incomplete_results") or int(data.get("total_count", 0)) > 100:
        raise RuntimeError("X_GITHUB_INVENTORY_INCOMPLETE")
    result = []
    for item in data.get("items", []):
        if not str(item.get("title", "")).startswith("[X-PUBLISH]"):
            continue
        row = parsed(item.get("body") or "")
        if row.get("platform") != "x" or row.get("account") != "lucasyahn" or row.get("test_fixture"):
            continue
        key = fingerprint(row)
        ref = hashlib.sha256(("x:lucasyahn:" + key).encode()).hexdigest()
        old = load(LEDGER + "/post-status?idempotency_key=" + key, secret)
        status = str(old.get("status") or "")
        if old.get("ok") is not True or status not in ("NOT_FOUND", "UNCERTAIN", "CONFIRMED"):
            raise RuntimeError("X_OLD_LEDGER_UNVERIFIED")
        comments = load(ROOT + "/issues/" + str(item["number"]) + "/comments?per_page=100", gh)
        if not isinstance(comments, list) or len(comments) >= 100:
            raise RuntimeError("X_OLD_ISSUE_COMMENTS_UNBOUNDED")
        bodies = " ".join(str(c.get("body") or "") for c in comments)
        started = any(mark in bodies for mark in (
            "X_SUBMISSION_STARTED_V1", "X_POST_SUBMISSION_STARTED_V1",
            "X_SUBMISSION_UNCERTAIN_V1", "X_LOCAL_SUBMISSION_STARTED_V1",
        ))
        if status == "NOT_FOUND" and started:
            status = "UNCERTAIN"
        url = str(old.get("post_url") or "")
        if status == "CONFIRMED" and not re.fullmatch(r"https://x.com/lucasyahn/status/[0-9]+", url):
            raise RuntimeError("X_OLD_CONFIRMED_URL_INVALID")
        result.append({"issue": int(item["number"]), "identity": ref,
                       "state": status, "post_url": url if status == "CONFIRMED" else None})
    print("X_LEGACY_INVENTORY=" + json.dumps(result, separators=(",", ":"), sort_keys=True))
    print("X_LEGACY_VERIFIED_COUNT=" + str(len(result)))


if __name__ == "__main__":
    main()
