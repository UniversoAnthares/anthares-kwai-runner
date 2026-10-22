#!/usr/bin/env python3
"""Cloud-only Pinterest QA incident loop. Never invokes Buffer createPost.

Every publisher run checks Neon receipts and the provider cooldown, then
updates the SAME QA P0 issue. A GitHub schedule retries after cooldown expiry.
Neither a successful workflow nor a Buffer draft qualifies as recovery.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import urllib.request

REPO = "UniversoAnthares/anthares-kwai-runner"
ISSUE = 507  # Existing Pinterest Buffer HTTP 429 P0; never create duplicates.
MARKER = "[PINTEREST-QA-AUTOLOOP]"
BASELINE_CONFIRMED = 7  # Snapshot before this recovery campaign.
VALID_RESULTS = {"PINS_RECONCILED", "PASS_NO_NEW_PIN", "SCHEDULED_NOT_PUBLISHED",
                 "WAITING_BUFFER_DELIVERY"}


def assess(evidence, counts, cooldown):
    if not isinstance(counts, dict) or not isinstance(cooldown, dict):
        return "QA_VISIBILITY_UNAVAILABLE", -1
    try:
        confirmed = int(counts.get("confirmed", 0))
        unresolved = sum(int(v) for k, v in counts.items() if k != "confirmed")
    except (TypeError, ValueError):
        return "QA_VISIBILITY_UNAVAILABLE", -1
    if evidence.get("worker_conclusion") != "success":
        return "EXECUTION_FAILED", unresolved
    if cooldown.get("active") is True or evidence.get("result") == "RATE_LIMIT_ISOLATED":
        return "COOLDOWN_HTTP_429", unresolved
    if (unresolved == 0 and confirmed > BASELINE_CONFIRMED and
            evidence.get("result") in VALID_RESULTS):
        return "PASS", 0
    if evidence.get("result") == "WAITING_BUFFER_DELIVERY":
        return "BUFFER_BACKPRESSURE", unresolved
    if evidence.get("result") == "UNVERIFIED_OR_FAILED":
        return "EXECUTION_UNVERIFIED", unresolved
    return "RETRY_UNTIL_CONFIRMED", unresolved


def should_report(previous, state, expiry, unresolved, now):
    if not previous:
        return True
    if previous.get("state") != state or previous.get("expiry") != str(expiry or ""):
        return True
    # One hourly heartbeat at most: no five-minute incident comment storms.
    try:
        last = datetime.fromisoformat(previous["at"].replace("Z", "+00:00"))
        return now - last >= timedelta(minutes=60)
    except (KeyError, TypeError, ValueError):
        return True


def request(method, endpoint, payload=None):
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("PINTEREST_QA_GITHUB_TOKEN_UNAVAILABLE")
    url = "https://api.github.com/repos/" + REPO + endpoint
    headers = {"Accept": "application/vnd.github+json",
               "Authorization": "Bearer " + token,
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "CortesPinterestQAAutoloop/1"}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(
            url, data=body, method=method, headers=headers), timeout=22) as r:
        return json.load(r) if r.status != 204 else {}


def main():
    from tools.cortes_buffer_pinterest_cloud import queue
    evidence_path = Path(os.getenv("PINTEREST_EVIDENCE_DIR", "/tmp/pinterest-evidence")) / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.exists() else {
        "result": "UNVERIFIED_OR_FAILED", "worker_conclusion": "failure"}
    try:
        counts = queue("stats")["counts"]
        cooldown = queue("cooldown-status")
    except Exception:
        # Never declare PASS when the authenticated Neon observation is absent.
        counts, cooldown = None, None
    state, unresolved = assess(evidence, counts, cooldown)
    expiry = cooldown.get("cooldown_until") if isinstance(cooldown, dict) else None
    issue = request("GET", "/issues/" + str(ISSUE))
    if not issue.get("title", "").startswith("[QA P0][pinterest] Buffer HTTP 429"):
        raise RuntimeError("PINTEREST_QA_ISSUE_IDENTITY_MISMATCH")
    now = datetime.now(timezone.utc)
    comments = request("GET", "/issues/" + str(ISSUE) + "/comments?per_page=100")
    prior = None
    for item in reversed(comments):
        body = str(item.get("body") or "")
        if body.startswith(MARKER + " "):
            try:
                prior = json.loads(body[len(MARKER) + 1:].split("\n", 1)[0])
            except (ValueError, TypeError):
                pass
            break
    result = {"state": state, "at": now.isoformat(), "expiry": str(expiry or ""),
              "unresolved": unresolved,
              "confirmed": (counts or {}).get("confirmed") if isinstance(counts, dict) else None,
              "run": os.environ.get("GITHUB_RUN_ID", "unknown")}
    if state != "PASS" and issue.get("state") == "closed":
        request("PATCH", "/issues/" + str(ISSUE), {"state": "open"})
    if should_report(prior, state, expiry, unresolved, now) or state == "PASS":
        comment = (MARKER + " " + json.dumps(result, separators=(",", ":")) + "\n\n"
                   + "QA automático Pinterest: observação autenticada do Neon e prova do publicador. "
                   + ("Aprovado: fila sem pendências, confirmação adicional por CAS Buffer/Pinterest; encerrar incidente."
                      if state == "PASS" else
                      "Ainda não comprovado. O publicador cloud repetirá a verificação após o cooldown "
                      "na próxima janela agendada; QA-P0 permanece aberto e é reavaliado pelo controlador. "
                      "Não reenviar estados incertos nem criar Pins durante cooldown.")
                   + "\nExecução: https://github.com/" + REPO + "/actions/runs/" + result["run"])
        request("POST", "/issues/" + str(ISSUE) + "/comments", {"body": comment})
    if state == "PASS" and issue.get("state") != "closed":
        request("PATCH", "/issues/" + str(ISSUE), {"state": "closed",
                                                "state_reason": "completed"})
    print("PINTEREST_QA_AUTOLOOP_STATE=" + state, flush=True)
    print("PINTEREST_QA_AUTOLOOP_UNRESOLVED=" + str(unresolved), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
