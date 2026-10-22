#!/usr/bin/env python3
"""Fallback source/long-video producer for Anthares X on authenticated Windows.

YouTube denies extraction from cloud datacenters even with cookies; the
authorized Windows origin can fetch it. This producer only queues 5-14m 16:9
media to the same GitHub queue. The hidden Anthares Browser publisher remains
the sole X submitter and the Northflank durable PostgreSQL ledger remains the
cross-platform idempotency authority.
"""
from __future__ import annotations
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests

REPO = "UniversoAnthares/anthares-kwai-runner"
BASE = "repos/" + REPO
ROOT = Path(os.getenv("ANTHARES_X_SOURCE_WORK", r"D:\AntharsWork\x-longform-source"))
WORK = ROOT / "work"
STATE = ROOT / "producer-status.json"
LOG = ROOT / "producer.log"
COOKIE = Path(r"D:\AntharsWork\anthares-clipper\runner-media\work\youtube-cookies.txt")
TZ = ZoneInfo("America/Campo_Grande")
CAP = 10
MAX_OPEN = 2


def checkpoint(phase, **kwargs):
    ROOT.mkdir(parents=True, exist_ok=True)
    previous = json.loads(STATE.read_text(encoding="utf8")) if STATE.exists() else {}
    value = {**previous, **kwargs, "phase": phase, "updated": datetime.now(TZ).isoformat()}
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=True, indent=2), encoding="utf8")
    os.replace(tmp, STATE)


def gh(path, method="GET", obj=None):
    args = ["gh", "api", BASE + path]
    data = None
    if method != "GET":
        args += ["-X", method, "--input", "-"]
        data = json.dumps(obj)
    r = subprocess.run(args, input=data, capture_output=True, text=True, timeout=55,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    if r.returncode:
        raise RuntimeError("GITHUB_API_" + str(r.returncode))
    return json.loads(r.stdout) if r.stdout.strip() else {}


def queue_inventory():
    items = []
    for page in range(1, 11):
        batch = gh(f"/issues?state=all&sort=created&direction=desc&per_page=100&page={page}")
        items.extend(x for x in batch if not x.get("pull_request"))
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("X_ISSUE_HISTORY_PAGINATION_INCOMPLETE")
    xitems = [x for x in items if str(x.get("title") or "").startswith("[X-PUBLISH]")]
    # Invalid or uncertain issues are isolated: they never block generation
    # of unrelated source windows. Their own fingerprints still stay reserved.
    from tools.x_publication_safety import _issue_payload
    open_queue = []
    for item in xitems:
        if item.get("state") != "open":
            continue
        parsed = _issue_payload(item.get("body"))
        if parsed.get("platform") != "x" or parsed.get("account") != "lucasyahn":
            continue
        if item.get("comments"):
            rows = gh("/issues/" + str(item["number"]) + "/comments?per_page=100")
            if len(rows) == 100:
                raise RuntimeError("X_OPEN_COMMENT_PAGINATION_INCOMPLETE")
            if any(any(marker in str(c.get("body") or "") for marker in
                       ("X_SUBMISSION_STARTED_V1", "X_POST_SUBMISSION_STARTED_V1",
                        "X_SUBMISSION_UNCERTAIN_V1"))
                   and (c.get("user") or {}).get("login") == "github-actions[bot]"
                   for c in rows):
                continue
        open_queue.append(item)
    windows = {}
    for issue in xitems:
        from tools.x_publication_safety import _issue_payload
        p = _issue_payload(issue.get("body") or "")
        if p.get("account") != "lucasyahn" or p.get("test_fixture"):
            continue
        source = p.get("source_id")
        start = p.get("scan_start")
        if source and start is not None:
            try:
                windows.setdefault(str(source), set()).add(int(start))
            except (TypeError, ValueError):
                continue
    confirmed_today = set()
    for issue in xitems:
        if issue.get("state") != "closed" or not issue.get("comments"):
            continue
        # Only bot-authenticated proofs validated against PostgreSQL count.
        comments = gh("/issues/" + str(issue["number"]) + "/comments?per_page=100")
        if len(comments) == 100:
            raise RuntimeError("X_PROOF_COMMENT_PAGINATION")
        for comment in comments:
            if (comment.get("user") or {}).get("login") != "github-actions[bot]":
                continue
            if "X_VIDEO_CONFIRMED_V1" not in str(comment.get("body") or ""):
                continue
            try:
                stamp = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))
                if stamp.astimezone(TZ).date() != datetime.now(TZ).date():
                    continue
                body = comment["body"]
                proof = json.loads(body[body.index("{"):])
                from tools.x_publication_safety import verified_post_url
                url = verified_post_url(str(proof.get("post_url") or ""))
                if proof.get("video_verified") and url:
                    confirmed_today.add(url)
            except (ValueError, TypeError, KeyError):
                continue
    return len(open_queue), len(confirmed_today), {
        source: sorted(v) for source, v in windows.items()
    }, xitems


def sync_source():
    ROOT.mkdir(parents=True, exist_ok=True)
    for target in ("x_cloud_prepare.py", "x_cloud_render.py", "tools/x_auto_plan.py",
                   "tools/x_publication_safety.py"):
        path = ROOT / target
        path.parent.mkdir(parents=True, exist_ok=True)
        info = gh("/contents/" + target + "?ref=main")
        raw = base64.b64decode("".join((info.get("content") or "").split()))
        if len(raw) < 250:
            raise RuntimeError("X_SOURCE_SYNC_TRUNCATED")
        temp = path.with_suffix(".synctmp")
        temp.write_bytes(raw)
        os.replace(temp, path)


def process(cmd, timeout, name, env=None):
    with LOG.open("a", encoding="utf8") as log:
        log.write("\nX_SOURCE_STAGE=" + name + "\n")
        log.flush()
        result = subprocess.run(cmd, cwd=str(WORK), env=env,
                                stdout=log, stderr=subprocess.STDOUT, timeout=timeout,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        log.write("\nX_SOURCE_STAGE_EXIT=" + name + ":" + str(result.returncode) + "\n")
    if result.returncode:
        raise RuntimeError("X_SOURCE_STAGE_FAILED_" + name)


def preflight_video(path):
    if not path.is_file() or path.stat().st_size < 100_000 or path.stat().st_size > 99_000_000:
        raise RuntimeError("X_LONGFORM_MEDIA_SIZE_INVALID")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height:format=duration",
                            "-of", "json", str(path)],
                           capture_output=True, text=True, timeout=40,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    if probe.returncode:
        raise RuntimeError("X_LONGFORM_FFPROBE_FAILED")
    data = json.loads(probe.stdout)
    stream = (data.get("streams") or [{}])[0]
    width, height = int(stream.get("width") or 0), int(stream.get("height") or 0)
    seconds = float((data.get("format") or {}).get("duration") or 0)
    if not (height > 0 and width > height and abs(width / height - 16 / 9) < .04
            and 300 <= seconds <= 840):
        raise RuntimeError("X_LONGFORM_MEDIA_POLICY_INVALID")
    return {"width": width, "height": height, "seconds": round(seconds, 3)}


def run_pipeline(windows):
    if not COOKIE.is_file() or COOKIE.stat().st_size < 100:
        raise RuntimeError("X_RESIDENTIAL_YOUTUBE_COOKIES_NOT_AVAILABLE")
    sync_source()
    WORK.mkdir(parents=True, exist_ok=True)
    if (WORK / "x-cloud-output.mp4").exists():
        (WORK / "x-cloud-output.mp4").unlink()
    env = os.environ.copy()
    env.update({
        "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1",
        "X_SOURCE_CHANNEL": "https://www.youtube.com/@UniversoAnthares/streams",
        "X_YT_COOKIE_FILE": str(COOKIE),
        "X_SCAN_START": "600", "X_SCAN_SECONDS": "780",
        "X_MIN_SOURCE_SECONDS": "1800",
        # The existing authorized Windows origin has a complete small model
        # in its local HuggingFace cache; the uncached base download stalled.
        "X_WHISPER_MODEL": "small",
        "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
        "X_SOURCE_WINDOWS_JSON": json.dumps(windows, separators=(",", ":")),
    })
    checkpoint("PREPARING")
    process([sys.executable, "-u", str(ROOT / "x_cloud_prepare.py")],
            2400, "PREPARE", env)
    checkpoint("PLANNING")
    process([sys.executable, "-u", str(ROOT / "tools/x_auto_plan.py")],
            150, "PLAN", env)
    checkpoint("RENDERING")
    process([sys.executable, "-u", str(ROOT / "x_cloud_render.py")],
            2600, "RENDER", env)
    result = json.loads((WORK / "x-render-result.json").read_text(encoding="utf8"))
    video = WORK / "x-cloud-output.mp4"
    info = preflight_video(video)
    source = result.get("source") or {}
    vid = str(source.get("video_id") or "")
    scan = int(result.get("scan_start") or 0)
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        raise RuntimeError("X_SOURCE_VIDEO_ID_INVALID")
    if scan in set(windows.get(vid, [])):
        raise RuntimeError("X_SOURCE_WINDOW_REUSED")
    caption = str(result.get("caption") or "").strip()
    lo, hi = float(result.get("segment_start")), float(result.get("segment_end"))
    if not (0 < len(caption) <= 240 and 300 <= hi - lo <= 840):
        raise RuntimeError("X_EDITORIAL_PLAN_INVALID")
    checkpoint("RENDERED",video_id=vid,scan_start=scan,
               segment_start=lo,segment_end=hi,caption=caption,media=info)
    return result, video, info


def enqueue(result, video, info, existing):
    source = result["source"]
    vid = source["video_id"]
    scan = int(result["scan_start"])
    lo, hi = float(result["segment_start"]), float(result["segment_end"])
    # Crash-safe: previous issue, including closed one, makes this a no-op.
    from tools.x_publication_safety import _issue_payload
    for issue in existing:
        row = _issue_payload(issue.get("body") or "")
        if (row.get("source_id") == vid
                and int(row.get("scan_start") or 0) == scan
                and abs(float(row.get("segment_start") or -1) - lo) < .05):
            checkpoint("ALREADY_QUEUED",issue_number=issue["number"])
            return
    tag = "x-longform-auto-" + datetime.now(TZ).strftime("%Y%m%d")
    name = "anthares-x-" + vid + "-" + str(scan) + "-" + str(int(lo)) + ".mp4"
    staging = ROOT / name
    if not staging.exists():
        shutil.copy2(video, staging)
    if preflight_video(staging) != info:
        raise RuntimeError("X_STAGED_MEDIA_MISMATCH")
    release = subprocess.run(["gh", "release", "view", tag, "-R", REPO, "--json", "assets",
                              "--jq", ".assets[].name"],
                             capture_output=True, text=True, timeout=55,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    if release.returncode:
        new = subprocess.run(["gh", "release", "create", tag, "-R", REPO,
                              "--target", "main", "--title", "Anthares X longform " + tag,
                              "--notes", "Automatically validated horizontal longform reserves."],
                             capture_output=True, text=True, timeout=80,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        if new.returncode:
            raise RuntimeError("X_RELEASE_CREATION_FAILED")
    if name not in release.stdout.splitlines():
        up = subprocess.run(["gh", "release", "upload", tag, str(staging), "-R", REPO],
                            capture_output=True, text=True, timeout=300,
                            creationflags=subprocess.CREATE_NO_WINDOW)
        if up.returncode and "already exists" not in up.stderr.lower():
            raise RuntimeError("X_RELEASE_UPLOAD_FAILED")
    url = "https://github.com/" + REPO + "/releases/download/" + tag + "/" + name
    microedit = result.get("microedit") or {}
    body = {
        "platform": "x", "account": "lucasyahn", "duration_class": "long",
        "caption": result["caption"], "media_url": url,
        "source_id": vid, "source_url": source.get("source_url"),
        "source_title": source.get("title"), "scan_start": scan,
        "segment_start": lo, "segment_end": hi,
        "microedit": {**microedit, "final_duration": info["seconds"]},
        "media_verified": info, "local_source_fallback": True
    }
    fence = chr(96) * 3
    title = f"[X-PUBLISH] local-origin-{vid}-{scan}-{int(lo)}"
    issue = gh("/issues", "POST", {
        "title": title,
        "body": fence + "json\n" + json.dumps(body, ensure_ascii=False, indent=2) + "\n" + fence
    })
    checkpoint("ISSUE_CREATED",issue_number=issue["number"],
               issue_url=issue.get("html_url"),media_url=url)
    print("X_LOCAL_SOURCE_ISSUE=" + str(issue.get("html_url")), flush=True)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    queued, confirmed, windows, all_x = queue_inventory()
    if queued >= MAX_OPEN:
        print("X_LOCAL_SOURCE_SKIPPED_PENDING_QUEUE=" + str(queued))
        return
    if queued + confirmed >= CAP:
        print("X_LOCAL_SOURCE_SKIPPED_DAILY_BUDGET=" + str(queued + confirmed))
        return
    current = json.loads(STATE.read_text(encoding="utf8")) if STATE.exists() else {}
    if current.get("phase") == "RENDERED":
        file = WORK / "x-cloud-output.mp4"
        data = WORK / "x-render-result.json"
        if file.exists() and data.exists():
            result = json.loads(data.read_text(encoding="utf8"))
            info = preflight_video(file)
            enqueue(result, file, info, all_x)
            return
    result, file, info = run_pipeline(windows)
    enqueue(result, file, info, all_x)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        today = datetime.now(TZ).date().isoformat()
        previous = json.loads(STATE.read_text(encoding="utf8")) if STATE.exists() else {}
        checkpoint("FAILED", error_type=type(exc).__name__,
                   error_code=str(exc)[:120])
        # One QA P0 notification per calendar day, never block other sources.
        if previous.get("qa_alert_day") != today:
            try:
                gh("/issues/380/comments", "POST", {"body":
                    "X_LOCAL_SOURCE_P0 day=" + today + " phase=" +
                    str(previous.get("phase") or "unknown")[:60] +
                    " error_type=" + type(exc).__name__})
                checkpoint("FAILED", qa_alert_day=today)
            except Exception:
                pass
        print("X_LOCAL_SOURCE_FAILED=" + type(exc).__name__, flush=True)
        raise SystemExit(2)
