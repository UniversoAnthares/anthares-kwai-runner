#!/usr/bin/env python3
"""Independent, read-only Instagram public-profile timeline reconciliation.

Only a complete chronological public Reels scan AND complete account Graph
listing can resolve a tagged uncertain CORTES job. A login gate, missing post
date, incomplete pagination or legacy caption always means INCONCLUSIVE.
The canonical Neon state is updated via signed OIDC; never retry a job here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.instagram_publish import InstagramClient
from tools.cortes_queue_ha import post, BackendUnavailable
from tools.cortes_instagram_direct_cloud import oidc, require_cloud

USERNAME = "universoanthares"
PROFILE_URL = "https://www.instagram.com/universoanthares/reels/"
TAG_CUTOVER = datetime.fromisoformat("2026-11-12T13:00:00+00:00")
MAX_PUBLIC_REELS = 250
MAX_GRAPH_PAGES = 8
PAGE_TIMEOUT_MS = 18000


def parsed_at(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("PUBLIC_RECONCILE_TIMESTAMP_REQUIRED")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("PUBLIC_RECONCILE_TIMEZONE_REQUIRED")
    return date.astimezone(timezone.utc)


def tag_for(job_id: str) -> str:
    if not re.fullmatch(r"cortes-fanout-instagram-[a-f0-9]{32}", job_id):
        raise ValueError("PUBLIC_RECONCILE_JOB_ID_INVALID")
    return "#antharescorte" + hashlib.sha256(job_id.encode()).hexdigest()[:12]


def clean_permalink(url: str) -> str | None:
    match = re.fullmatch(r"https://(?:www\.)?instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+)/?", str(url))
    return "https://www.instagram.com/reel/" + match.group(1) + "/" if match else None


def cover(start: datetime, values: list[dict], *, margin: timedelta = timedelta(minutes=20)) -> tuple[bool, str | None, str | None]:
    timestamps = []
    for row in values:
        try:
            timestamps.append(parsed_at(row["timestamp"]))
        except (ValueError, TypeError, KeyError):
            return False, None, None
    if not timestamps:
        return False, None, None
    oldest, newest = min(timestamps), max(timestamps)
    return (
        oldest <= start - margin and newest >= start + margin,
        oldest.isoformat().replace("+00:00", "Z"),
        newest.isoformat().replace("+00:00", "Z"),
    )


def scan_public_profile(start: datetime) -> dict:
    """Walk the visible profile grid and open every Reel until time coverage."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"complete": False, "reason": "PLAYWRIGHT_NOT_INSTALLED"}
    # An anonymous context is forbidden. Use ONLY the existing authorized
    # persistent session; browser authentication and account view are mandatory.
    profile = os.environ.get("CORTES_INSTAGRAM_AUTH_PROFILE", "").strip()
    expected = r"D:\AntharsWork\browser-profiles\AntharesInstagram"
    if not profile or os.path.normcase(os.path.normpath(profile)) != os.path.normcase(os.path.normpath(expected)):
        return {"complete": False, "reason": "PERSISTENT_AUTH_PROFILE_REQUIRED"}
    if not Path(profile).is_dir():
        return {"complete": False, "reason": "PERSISTENT_AUTH_PROFILE_NOT_FOUND"}
    posts: dict[str, dict] = {}
    try:
        with sync_playwright() as pw:
            context = pw.chromium.launch_persistent_context(
                user_data_dir=profile, channel="chrome", headless=True,
                viewport={"width": 1200, "height": 900}, locale="pt-BR",
                args=["--no-first-run", "--disable-notifications", "--mute-audio"])
            try:
                grid = context.pages[0] if context.pages else context.new_page()
                # The settings page is private; a login redirect proves the
                # existing profile is not authenticated in this session.
                grid.goto("https://www.instagram.com/accounts/edit/",
                          wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
                grid.wait_for_timeout(900)
                if ("/accounts/login/" in grid.url or "/challenge/" in grid.url
                        or grid.locator('input[name="username"]').count()):
                    return {"complete": False, "reason": "PERSISTENT_PROFILE_LOGIN_REQUIRED"}
                # Avoid accepting an arbitrary public/redirect page as login.
                if "/accounts/" not in grid.url:
                    return {"complete": False, "reason": "PERSISTENT_PROFILE_AUTH_UNVERIFIED"}
                grid.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
                if "/accounts/login/" in grid.url or "/challenge/" in grid.url:
                    return {"complete": False, "reason": "PUBLIC_PROFILE_ACCESS_GATE"}
                grid.wait_for_timeout(1700)
                if grid.locator('input[name="username"]').count():
                    return {"complete": False, "reason": "PUBLIC_PROFILE_LOGIN_REQUIRED"}
                candidates: list[str] = []
                seen: set[str] = set()
                stagnant = 0
                # Collect each URL before scrolling: Instagram virtualizes grid rows.
                for _ in range(180):
                    hrefs = grid.locator('a[href*="/reel/"]').evaluate_all(
                        "(anchors) => anchors.map(a => a.href)")
                    added = 0
                    for link in hrefs:
                        normalized = clean_permalink(link)
                        if normalized and normalized not in seen:
                            seen.add(normalized)
                            candidates.append(normalized)
                            added += 1
                    if len(candidates) >= MAX_PUBLIC_REELS:
                        break
                    stagnant = stagnant + 1 if added == 0 else 0
                    grid.mouse.wheel(0, 1000)
                    grid.wait_for_timeout(140)
                    if "/accounts/login/" in grid.url or stagnant >= 9:
                        break
                if "/accounts/login/" in grid.url or not candidates:
                    return {"complete": False, "reason": "PUBLIC_PROFILE_GRID_UNAVAILABLE"}
                view = context.new_page()
                for url in candidates:
                    try:
                        view.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
                        if "/accounts/login/" in view.url or "/challenge/" in view.url:
                            return {"complete": False, "reason": "PUBLIC_REEL_ACCESS_GATE"}
                        details = view.evaluate("""() => {
                           let t = document.querySelector('time[datetime]')?.getAttribute('datetime')
                                  || document.querySelector('meta[property="article:published_time"]')?.content
                                  || null;
                           let caption = document.querySelector('meta[property="og:description"]')?.content
                                   || document.querySelector('h1')?.innerText || '';
                           return {timestamp: t, caption: caption};
                        }""")
                        if not details or not details.get("timestamp"):
                            return {"complete": False, "reason": "PUBLIC_REEL_DATE_MISSING"}
                        posts[url] = {"permalink": url, "timestamp": details["timestamp"],
                                      "caption": details.get("caption", "")}
                        covered, _, _ = cover(start, list(posts.values()))
                        if covered:
                            # All previously loaded grid URLs were individually visited,
                            # and we reached beyond the expected publication window.
                            break
                    except Exception:
                        return {"complete": False, "reason": "PUBLIC_REEL_READ_FAILED"}
                covered, oldest, newest = cover(start, list(posts.values()))
                return {"complete": covered, "authenticated": True, "profile": "AntharesInstagram",
                        "reason": "COVERED" if covered else "PUBLIC_TIMELINE_INCOMPLETE",
                        "items": list(posts.values()), "count": len(posts),
                        "oldest_at": oldest, "newest_at": newest,
                        "grid_count": len(candidates)}
            finally:
                context.close()
    except Exception:
        return {"complete": False, "reason": "PUBLIC_BROWSER_UNAVAILABLE"}


def scan_graph_media(client: InstagramClient, start: datetime) -> dict:
    """Independent account-media readback, bounded to the same date range."""
    rows: list[dict] = []
    after = None
    for _ in range(MAX_GRAPH_PAGES):
        query = {"fields": "id,permalink,timestamp,caption,media_type", "limit": "100"}
        if after:
            query["after"] = after
        response = client._request("GET", f"{client.user_id}/media", query=query)
        batch = response.get("data") or []
        if not isinstance(batch, list):
            return {"complete": False, "reason": "GRAPH_MEDIA_INVALID"}
        for row in batch:
            permalink = clean_permalink(str(row.get("permalink") or ""))
            if permalink and row.get("timestamp") and str(row.get("id", "")).isdigit():
                rows.append({"permalink": permalink, "id": str(row["id"]),
                             "timestamp": row["timestamp"],
                             "caption": str(row.get("caption") or "")})
        covered, oldest, newest = cover(start, rows)
        if covered:
            return {"complete": True, "items": rows, "count": len(rows),
                    "oldest_at": oldest, "newest_at": newest}
        cursor = (response.get("paging") or {}).get("cursors") or {}
        next_after = cursor.get("after")
        if not batch or not next_after or next_after == after:
            break
        after = str(next_after)
    return {"complete": False, "reason": "GRAPH_TIMELINE_INCOMPLETE"}


def decide(job: dict, public: dict, graph: dict, observed_at: datetime | None = None) -> dict | None:
    started = parsed_at(job.get("publication_started_at"))
    # Historical captions without the per-segment tag cannot be matched exactly.
    if started < TAG_CUTOVER:
        return None
    if not public.get("complete") or not graph.get("complete"):
        return None
    tag = tag_for(str(job["id"]))
    pub = [p for p in public["items"] if tag.lower() in str(p.get("caption","")).lower()]
    own = [p for p in graph["items"] if tag.lower() in str(p.get("caption","")).lower()]
    if len(pub) > 1 or len(own) > 1:
        return None
    if bool(pub) != bool(own):
        return None
    common = bool(pub and own and pub[0]["permalink"] == own[0]["permalink"])
    proof = {
        "username": USERNAME, "origin": "instagram_public_profile",
        "profile_url": PROFILE_URL, "complete": True, "graph_complete": True,
        "observed_at": (observed_at or datetime.now(timezone.utc)).isoformat().replace("+00:00","Z"),
        "tag": tag, "scanned_count": public["count"],
        "graph_scanned_count": graph["count"],
        "oldest_at": public["oldest_at"], "newest_at": public["newest_at"],
        "graph_oldest_at": graph["oldest_at"],
        "matching_caption_tag": bool(pub), "graph_matching_tag": bool(own),
    }
    if common:
        proof.update(matched_permalink=pub[0]["permalink"],
                     graph_permalink=own[0]["permalink"],
                     graph_media_id=own[0]["id"])
        return {"id": job["id"], "decision": "visible",
                "permalink": pub[0]["permalink"], "media_id": own[0]["id"], "proof": proof}
    if not pub and not own and started <= datetime.now(timezone.utc) - timedelta(hours=36):
        # Before declaring absence, every public Reel in the fully covered
        # interval must exist in the account-owner Graph feed as well. A
        # truncated OpenGraph caption or incomplete public listing is not
        # trustworthy negative evidence unless the two listings are in parity.
        start_edge = started - timedelta(minutes=20)
        end_edge = datetime.now(timezone.utc)
        public_links = {p.get("permalink") for p in public["items"]
                        if start_edge <= parsed_at(p["timestamp"]) <= end_edge}
        graph_links = {p.get("permalink") for p in graph["items"]
                       if start_edge <= parsed_at(p["timestamp"]) <= end_edge}
        if not public_links or not public_links.issubset(graph_links):
            return None
        proof["public_graph_profile_parity"] = True
        return {"id": job["id"], "decision": "absent", "proof": proof}
    return None


def stored_timestamp(job: dict) -> datetime | None:
    evidence=job.get("confirmation_evidence") or {}
    if isinstance(evidence,str):
        try:evidence=json.loads(evidence)
        except (ValueError,TypeError):evidence={}
    raw=job.get("publication_started_at") or evidence.get("submitted_at")
    try:
        return parsed_at(raw)
    except (KeyError,ValueError,TypeError):
        return None


def action_prepare() -> int:
    """OIDC hosted job saves only the earliest uncertain timestamp for browser scan."""
    require_cloud()
    pending=post("instagram-direct-pending", {"limit":50}, oidc)
    if not pending.get("ok") or pending.get("target_key")!="instagram:universoanthares":
        raise RuntimeError("PUBLIC_RECONCILE_QUEUE_READ_FAILED")
    dates=[d for j in pending.get("items",[]) if (d:=stored_timestamp(j))]
    path=Path(os.environ["CORTES_INSTAGRAM_WINDOW_OUTPUT"])
    body={"oldest_at":min(dates).isoformat() if dates else None,
          "candidates":len(dates),"created_at":datetime.now(timezone.utc).isoformat(),
          "target_key":"instagram:universoanthares"}
    path.write_text(json.dumps(body),encoding="utf-8")
    print(json.dumps({"public_reconcile":"WINDOW_PREPARED","candidates":len(dates)}),flush=True)
    return 0


def action_scan() -> int:
    """Windows-only read: use the existing logged-in profile, publish metadata only."""
    filename=Path(os.environ["CORTES_INSTAGRAM_WINDOW_INPUT"])
    params=json.loads(filename.read_text(encoding="utf-8"))
    if params.get("target_key")!="instagram:universoanthares":
        raise RuntimeError("RECONCILE_WINDOW_INVALID")
    oldest=params.get("oldest_at")
    if not oldest:
        result={"complete":True,"empty":True,"authenticated":False,"reason":"NO_UNCERTAIN_WITH_TIMESTAMP"}
    else:
        result=scan_public_profile(parsed_at(oldest))
    result["captured_at"]=datetime.now(timezone.utc).isoformat()
    Path(os.environ["CORTES_INSTAGRAM_PROFILE_OUTPUT"]).write_text(
        json.dumps(result,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"public_reconcile":"PROFILE_SCANNED","complete":result.get("complete"),
                      "authenticated":result.get("authenticated",False),
                      "reason":result.get("reason"),"reels":result.get("count",0)}),flush=True)
    return 0


def main() -> int:
    # Only the hosted GitHub OIDC role can update the canonical Neon ledger.
    client = require_cloud()
    # Require fresh authenticated profile readback before even examining jobs:
    # anonymous or expired browser state can never classify an uncertain Reel.
    snapshot=post("instagram-direct-profile-snapshot", {}, oidc)
    if not snapshot.get("ok") or not snapshot.get("available"):
        print(json.dumps({"public_reconcile":"AUTHENTICATED_PROFILE_REQUIRED",
                          "reason":snapshot.get("reason","NO_FRESH_AUTHENTICATED_SCAN")}),flush=True)
        return 0
    pending = post("instagram-direct-pending", {"limit": 50}, oidc)
    if not pending.get("ok") or pending.get("target_key") != "instagram:universoanthares":
        raise RuntimeError("PUBLIC_RECONCILE_QUEUE_REJECTED")
    jobs = pending.get("items") or []
    eligible = [j for j in jobs if stored_timestamp(j) is not None]
    if not eligible:
        print(json.dumps({"public_reconcile": "NO_TIMESTAMP_CANDIDATES",
                          "unresolved": len(jobs)}), flush=True)
        return 0
    oldest = min(stored_timestamp(j) for j in eligible)
    data=snapshot.get("scan") or {}
    items=data.get("posts") or []
    if isinstance(items,str):
        items=json.loads(items)
    public={"complete":True,"authenticated":True,"profile":data.get("profile_name"),
            "captured_at":data.get("captured_at"),"oldest_at":data.get("oldest_at"),
            "newest_at":data.get("newest_at"),"count":len(items),"items":items}
    if (public.get("profile")!="AntharesInstagram"
            or datetime.now(timezone.utc)-parsed_at(public.get("captured_at"))>timedelta(minutes=60)
            or parsed_at(public.get("oldest_at"))>oldest-timedelta(minutes=20)):
        print(json.dumps({"public_reconcile":"AUTHENTICATED_PROFILE_WINDOW_MISSING"}),flush=True)
        return 0
    if not public.get("complete"):
        print(json.dumps({"public_reconcile": "INCONCLUSIVE_PUBLIC_PROFILE",
                          "reason": public.get("reason")}), flush=True)
        return 0
    graph = scan_graph_media(client, oldest)
    if not graph.get("complete"):
        print(json.dumps({"public_reconcile": "INCONCLUSIVE_GRAPH_READBACK",
                          "reason": graph.get("reason")}), flush=True)
        return 0
    total = 0
    for job in eligible:
        action = decide(job, public, graph)
        if not action:
            continue
        result = post("instagram-direct-reconcile", action, oidc)
        if result.get("ok"):
            total += 1
    print(json.dumps({"public_reconcile": "FINISHED",
                      "decisions_recorded": total,
                      "public_items": public["count"],
                      "graph_items": graph["count"]}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        operation=sys.argv[1] if len(sys.argv)>1 else "reconcile"
        handler={"prepare":action_prepare,"profile-scan":action_scan,
                 "reconcile":main}.get(operation)
        if handler is None:
            raise RuntimeError("PUBLIC_RECONCILE_MODE_INVALID")
        raise SystemExit(handler())
    except Exception as error:
        reason=str(error)[:90] if isinstance(error,BackendUnavailable) else type(error).__name__
        print(json.dumps({"public_reconcile": "FAILED_SAFE",
                          "reason": reason}), file=sys.stderr)
        raise SystemExit(2)
