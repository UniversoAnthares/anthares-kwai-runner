#!/usr/bin/env python3
"""Pinterest local web-UI consumer: Neon fenced lease -> Chrome CDP -> verified Pin.

The direct Pinterest API and Buffer tokens are not used.  A two-phase child
process obtains editorial/board/video readiness BEFORE Neon status='started'.
Only a confirmed public Pin URL receives status='confirmed'; ambiguous results
remain 'uncertain' and never get blindly retried.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue as threading_queue
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import urllib.request
import urllib.error
from urllib.parse import urlparse

NEON_BROWSER_QUEUE = "https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/"
def call(action: str, payload: dict):
    """Neon direct, device-scoped Pinterest actions; never silently falls back to Vercel."""
    if action not in {"lease", "start", "fail", "confirm", "stats", "media-invalid", "metadata-pending", "metadata-enrich", "qa-media-pending", "qa-media-result"}:
        raise ValueError("PINTEREST_NEON_ACTION_NOT_ALLOWED")
    url = os.getenv("CORTES_PINTEREST_NEON_URL", NEON_BROWSER_QUEUE).rstrip("/") + "/"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech":
        raise RuntimeError("PINTEREST_NEON_ENDPOINT_NOT_PINNED")
    token = os.getenv("ANTHARES_DEVICE_TOKEN", "").strip()
    if len(token) < 40:
        raise RuntimeError("PINTEREST_DEVICE_AUTH_MISSING")
    request = urllib.request.Request(url + "?action=browser-" + action,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Authorization": "Bearer " + token,
                 "X-Anthares-Device": "DESKTOP-FTDK0HP",
                 "Content-Type": "application/json",
                 "User-Agent": "AntharesPinterestBrowserLocal/1.0"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=35) as result:
            return json.load(result)
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read().decode("utf-8"))
            return result if isinstance(result, dict) else {"ok": False, "error": "NEON_HTTP_" + str(exc.code)}
        except (ValueError, UnicodeError):
            return {"ok": False, "error": "NEON_HTTP_" + str(exc.code)}
from anthares_publisher.editorial import prepare_publication_metadata

ACCOUNT = "lucasyahn"
TARGET = "pinterest:" + ACCOUNT
OWNER = "pinterest-browser:" + (os.getenv("ANTHARES_DEVICE_ID") or "DESKTOP-FTDK0HP")
CDP = ROOT / "tools" / "cortes_pinterest_browser_ui.mjs"
EVENTS = Path(os.getenv("CORTES_PINTEREST_LOCAL_EVENTS", str(ROOT / "pinterest-browser-events.log")))
NODE = os.getenv("CORTES_NODE_EXE", "node")
DRAFT_GUARD = Path(os.getenv("CORTES_PINTEREST_DRAFT_GUARD",
    str(ROOT / ".pinterest-unreconciled-upload.json")))


def draft_guard_mark(drafts_before: int, job_id: str) -> None:
    """Persist a pre-submit risk before invoking a browser that may save a draft."""
    value = {
        "kind": "PINTEREST_DRAFT_RECONCILIATION_REQUIRED",
        "baseline": int(drafts_before),
        "job_hash": hashlib.sha256(job_id.encode("utf-8")).hexdigest(),
        "created_at": int(time.time())
    }
    DRAFT_GUARD.parent.mkdir(parents=True, exist_ok=True)
    with DRAFT_GUARD.open("x", encoding="utf-8") as output:
        json.dump(value, output, separators=(",", ":"))


def draft_guard_clear_after_confirmation(job_id: str) -> None:
    """Clear only the guard for the exact job after verified publication."""
    value = json.loads(DRAFT_GUARD.read_text(encoding="utf-8"))
    if value.get("job_hash") != hashlib.sha256(job_id.encode("utf-8")).hexdigest():
        raise RuntimeError("PINTEREST_DRAFT_GUARD_JOB_MISMATCH")
    DRAFT_GUARD.unlink()


def draft_guard_blocked(drafts: int) -> bool:
    """Keep a potentially saved draft fenced until explicitly reconciled by QA."""
    if not DRAFT_GUARD.exists():
        return False
    try:
        value = json.loads(DRAFT_GUARD.read_text(encoding="utf-8"))
        if (value.get("kind") != "PINTEREST_DRAFT_RECONCILIATION_REQUIRED"
                or not 0 <= int(value.get("baseline", -1)) <= 50
                or not isinstance(value.get("job_hash"), str)
                or len(value["job_hash"]) != 64):
            raise ValueError("invalid_guard")
    except (ValueError, KeyError, TypeError, OSError):
        qa_incident("PINTEREST_DRAFT_GUARD_INVALID")
        return True
    # A recorded upload can create a draft even if Publish never becomes ready.
    # Count changes alone cannot identify it. Only a positive reconciliation
    # of the exact job may clear this file; never clear on a timer or restart.
    log("PINTEREST_DRAFT_GUARD_ACTIVE", count=int(drafts), baseline=value["baseline"])
    qa_incident("PINTEREST_UNRECONCILED_DRAFT")
    return True



def log(action: str, **info):
    event = {"when": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "action": action, **info}
    try:
        EVENTS.parent.mkdir(parents=True, exist_ok=True)
        with EVENTS.open("a", encoding="utf-8") as h:
            h.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass
    print(json.dumps(event, ensure_ascii=False), flush=True)


def qa_incident(reason: str):
    """Write a sanitized QA P0 incident, without secret/caption/video content."""
    base = Path(os.getenv("CORTES_PINTEREST_QA_DIR",
                          r"D:\AntharsWork\cortes-social-browser-20261020\qa-incidents"))
    try:
        base.mkdir(parents=True, exist_ok=True)
        data = {"priority": "P0", "network": "pinterest",
                "category": "BROWSER_PUBLICATION_BLOCKED",
                "reason": reason[:125], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        tmp = base / "pinterest-browser-p0.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, base / "pinterest-browser-p0.json")
        qa_central_incident(reason[:90], base)
    except OSError:
        pass


def media_missing(url: str) -> bool:
    """Identify an actual 404, not a transient upload or connection failure."""
    req = urllib.request.Request(url, method="HEAD", headers={
        "User-Agent": "AntharesPinterestMediaPreflight/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=16) as response:
            return False
    except urllib.error.HTTPError as exc:
        return exc.code == 404


def qa_media_incident(job_id: str, media_url: str):
    """Push sanitized incident to central QA, without any secret or media body."""
    fingerprint = hashlib.sha256(job_id.encode("utf-8")).hexdigest()[:24]
    qa_incident("PINTEREST_MEDIA_404_" + fingerprint)
    safe_id = job_id[:125]
    title = "[QA P0][pinterest] Mídia 404 — corrigir origem e validar republicação"
    body = ("QA-P0-FINGERPRINT:" + fingerprint + "\\n\\n"
            "PRIORIDADE P0: origem de vídeo HTTP 404, bloqueio individual, "
            "não bloquear a fila dos demais vídeos.\\n\\n"
            "Job: " + safe_id + "\\n"
            "SHA-256 da URL: " + hashlib.sha256(media_url.encode()).hexdigest() + "\\n"
            "AÇÃO: corrigir mídia no WordPress, verificar HTTP 200, "
            "reprocessar apenas se o ledger autorizar, nunca publicar duplicado. "
            "Se não for reparada no dia seguinte, descartar.\\n")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        check = subprocess.run(["gh", "issue", "list", "--repo",
            "UniversoAnthares/anthares-kwai-runner", "--state", "all",
            "--search", fingerprint, "--json", "number", "--limit", "5"],
            capture_output=True, text=True, timeout=18, creationflags=flags)
        if check.returncode == 0 and json.loads(check.stdout):
            return
        if check.returncode != 0:
            log("PINTEREST_QA_CENTRAL_UNAVAILABLE", job_id=job_id)
            return
        created = subprocess.run(["gh", "issue", "create", "--repo",
            "UniversoAnthares/anthares-kwai-runner", "--title", title,
            "--body", body, "--label", "QA-P0", "--label", "publication-failure"],
            capture_output=True, text=True, timeout=25, creationflags=flags)
        log("PINTEREST_QA_CENTRAL_SENT" if created.returncode == 0
            else "PINTEREST_QA_CENTRAL_UNAVAILABLE", job_id=job_id)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        log("PINTEREST_QA_CENTRAL_UNAVAILABLE", job_id=job_id)


def qa_central_incident(reason: str, base: Path):
    """Deduplicated GitHub QA ticket; never include cookies, captions or secrets."""
    from datetime import datetime
    local_day = datetime.now().strftime("%Y-%m-%d")
    fingerprint = hashlib.sha256(("pinterest|" + reason + "|" + local_day).encode()).hexdigest()[:24]
    marker = base / ("pinterest-p0-" + fingerprint + ".sent")
    if marker.exists():
        return
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    gh = ["gh", "issue"]
    repo = "UniversoAnthares/anthares-kwai-runner"
    try:
        listed = subprocess.run(gh + ["list", "--repo", repo, "--state", "all", "--search",
            fingerprint, "--json", "number", "--limit", "5"], capture_output=True,
            text=True, timeout=18, creationflags=flags)
        if listed.returncode != 0:
            return
        if not json.loads(listed.stdout):
            body = ("QA-P0-FINGERPRINT:" + fingerprint + "\\n\\n"
                    "Publicador Pinterest interrompido antes da fase de envio. "
                    "Razão sanitizada: " + reason + "\\n"
                    "Investigar imediatamente e corrigir o código sem duplicar posts. "
                    "Os demais vídeos não devem ser bloqueados.\\n")
            created = subprocess.run(gh + ["create", "--repo", repo, "--title",
                "[QA P0][pinterest] Falha operacional " + reason,
                "--body", body, "--label", "QA-P0", "--label", "publication-failure"],
                capture_output=True, text=True, timeout=22, creationflags=flags)
            if created.returncode != 0:
                return
        marker.write_text(local_day, encoding="utf8")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass


def node_run(*args, timeout=50):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    p = subprocess.run([NODE, str(CDP), *args], stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, cwd=str(ROOT),
                       creationflags=flags)
    lines = [json.loads(x) for x in p.stdout.splitlines() if x.strip().startswith("{")]
    return lines[-1] if lines else {"status": "BLOCKED", "reason": "BROWSER_NO_RESPONSE"}


def validate_job(row):
    if not isinstance(row, dict) or row.get("target_key") != TARGET:
        raise ValueError("PINTEREST_WRONG_TARGET")
    if row.get("duration_class") != "short":
        raise ValueError("PINTEREST_NOT_SHORT")
    data = row.get("payload") or {}
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict) or data.get("account_id") != ACCOUNT or data.get("platform") != "pinterest":
        raise ValueError("PINTEREST_WRONG_ACCOUNT")
    meta = prepare_publication_metadata(data, title_limit=100)
    url = str(data.get("media_url") or data.get("video_url") or "")
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"anthares.us", "www.anthares.us"} or \
            parsed.username or parsed.password or not parsed.path.lower().endswith(".mp4"):
        raise ValueError("PINTEREST_UNTRUSTED_MEDIA")
    seconds = float(data.get("duration_seconds") or 0)
    if not 30 <= seconds <= 90:
        raise ValueError("PINTEREST_DURATION_INVALID")
    return {"platform": "pinterest", "account_id": ACCOUNT, "media_url": url,
            "title": meta["title"], "description": meta["description"][:500]}


def child_protocol(jobfile: Path, fence: dict):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen([NODE, str(CDP), "--publish", str(jobfile)],
                            cwd=str(ROOT), text=True, encoding="utf-8",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, bufsize=1, creationflags=flags)
    messages: threading_queue.Queue = threading_queue.Queue()
    def reader():
        try:
            for line in proc.stdout:
                try: messages.put(json.loads(line))
                except ValueError: continue
        finally:
            messages.put({"phase": "_CHILD_EXIT"})
    th = threading.Thread(target=reader, daemon=True)
    th.start()
    started = False
    submitted = False
    upload_attempted = False
    try:
        deadline = time.monotonic() + 540
        while time.monotonic() < deadline:
            try: msg = messages.get(timeout=min(8, max(0.1, deadline - time.monotonic())))
            except threading_queue.Empty:
                if proc.poll() is not None:
                    break
                continue
            if msg.get("phase") == "PREPARED":
                result = call("start", fence)
                if not result.get("ok"):
                    log("PINTEREST_START_REJECTED")
                    try: proc.stdin.write("STOP\n"); proc.stdin.flush()
                    except OSError: pass
                    return False, False, None
                started = True
                proc.stdin.write("GO\n")
                proc.stdin.flush()
            elif msg.get("phase") == "UPLOAD_ATTEMPTED":
                upload_attempted = True
            elif msg.get("phase") == "PREPARE_DIAGNOSTIC":
                # The browser emits only button-state and count metadata, never
                # account content, video, cookies, or captions.
                info = msg.get("state") or {}
                if isinstance(info, dict):
                    log("PINTEREST_EDITOR_DIAGNOSTIC",
                        buttons=(info.get("buttons") or [])[:5],
                        invalidCount=info.get("invalidCount"),
                        pendingUploads=info.get("pendingUploads"),
                        videoCount=info.get("videoCount"))
            elif msg.get("phase") == "SUBMIT_CLICKED":
                submitted = True
                log("PINTEREST_SUBMIT_CLICKED", job_id=fence["id"])
            elif msg.get("status") == "CONFIRMED":
                return started, True, msg
            elif msg.get("status") == "BLOCKED_OR_UNCERTAIN":
                log("PINTEREST_UI_BLOCKED", reason=msg.get("reason", "unknown"))
                if not upload_attempted:
                    # The child explicitly failed before file input; no draft created.
                    try:
                        draft_guard_clear_after_confirmation(fence["id"])
                    except (OSError, KeyError, ValueError, RuntimeError):
                        qa_incident("PINTEREST_DRAFT_GUARD_REQUIRES_QA")
                qa_incident(str(msg.get("reason", "unknown")))
                return started, False, None
            elif msg.get("phase") == "_CHILD_EXIT":
                break
        qa_incident("PINTEREST_UI_TIMEOUT_OR_NO_FINAL_EVIDENCE")
        return started, False, None
    finally:
        if proc.poll() is None:
            proc.kill()
        try: proc.communicate(timeout=8)
        except (subprocess.TimeoutExpired, OSError): pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if os.getenv("CORTES_PINTEREST_LOCAL_ENABLED") != "1":
        log("DISABLED")
        return 0
    if os.getenv("ANTHARES_SOCIAL_COMMIT") != "1":
        log("DISARMED")
        return 0
    if not os.getenv("ANTHARES_DEVICE_TOKEN", "").strip():
        log("AUTH_REQUIRED_NEON_DEVICE")
        return 3
    try:
        status = node_run("--preflight", timeout=48)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        status = {"status": "BLOCKED", "reason": "CDP_PREFLIGHT_FAILURE"}
    if status.get("status") != "READY":
        reason = str(status.get("reason") or "PINTEREST_BROWSER_LOGIN_REQUIRED")
        log("BROWSER_NOT_READY", reason=reason)
        qa_incident(reason)
        return 3
    drafts = int(status.get("draft_count") or 0)
    if drafts >= 49:
        # Prevent Pinterest's documented 50-draft limit from causing another
        # orphan upload. QA must reconcile existing unpublished drafts first.
        log("PINTEREST_DRAFT_CAPACITY_PAUSED", count=drafts)
        qa_incident("PINTEREST_DRAFT_CAPACITY_EXHAUSTED")
        return 6
    if args.preflight:
        log("PINTEREST_BROWSER_READY", account=ACCOUNT, draft_count=drafts)
        return 0
    if draft_guard_blocked(drafts):
        return 6
    leased = call("lease", {"target_key": TARGET, "owner": OWNER, "lease_seconds": 900})
    if not leased.get("ok"):
        log("QUEUE_LEASE_REJECTED")
        return 4
    row = leased.get("job")
    if not row:
        log("IDLE_NO_BROWSER_LANE_CUTS")
        return 0
    fence = {"id": row["id"], "owner": OWNER, "lease_generation": row["lease_generation"]}
    if leased.get("delivery_route") != "browser":
        # An outdated queue backend MUST NOT hand arbitrary jobs to this worker.
        try: call("fail", fence)
        except Exception: pass
        log("QUEUE_BROWSER_ROUTE_NOT_ACKNOWLEDGED")
        qa_incident("QUEUE_BROWSER_ROUTE_NOT_ACKNOWLEDGED")
        return 4
    try:
        job = validate_job(row)
        if media_missing(job["media_url"]):
            # No upload or submit occurred: notify QA, quarantine only this ID.
            reported = call("media-invalid", fence)
            if reported.get("ok"):
                log("PINTEREST_MEDIA_ISOLATED", job_id=fence["id"],
                    status=reported.get("job", {}).get("status"))
                qa_media_incident(fence["id"], job["media_url"])
                return 0
            raise RuntimeError("PINTEREST_MEDIA_QUARANTINE_REJECTED")
        # A browser may autosave an upload before any submit. Persist a latch
        # before opening the editor, so a crash cannot silently cause repeats.
        draft_guard_mark(drafts, fence["id"])
        with tempfile.TemporaryDirectory(prefix="cortes-pin-") as folder:
            filename = Path(folder) / "job.json"
            filename.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
            started, success, result = child_protocol(filename, fence)
        if success and result and started:
            remote_id = str(result.get("remote_id") or "")
            permalink = str(result.get("permalink") or "")
            if remote_id.isdecimal() and permalink == "https://br.pinterest.com/pin/" + remote_id + "/":
                confirmed = call("confirm", {**fence, "remote_id": remote_id,
                    "confirmation_evidence": {"kind": "pinterest_browser_verified_pin",
                       "verified_id": remote_id, "permalink": permalink, "route": "browser"}})
                if confirmed.get("ok"):
                    try:
                        draft_guard_clear_after_confirmation(fence["id"])
                    except (OSError, KeyError, ValueError, RuntimeError):
                        qa_incident("PINTEREST_DRAFT_GUARD_REQUIRES_QA")
                    log("PIN_CONFIRMED", pin=permalink, job_id=fence["id"])
                    return 0
            qa_incident("PINTEREST_NEON_CONFIRMATION_UNCERTAIN")
    except Exception as exc:
        log("PINTEREST_WORKER_ERROR", error=type(exc).__name__)
        qa_incident(type(exc).__name__)
    # For started jobs, fail() preserves UNCERTAIN, never auto-retries.
    try: call("fail", fence)
    except Exception: pass
    return 5


if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as exc:
        log("PINTEREST_WORKER_FAILED", error=type(exc).__name__)
        qa_incident(type(exc).__name__)
        sys.exit(5)
