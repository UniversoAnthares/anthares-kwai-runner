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
from tools.cortes_queue_ha import post
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
    posts: dict[str, dict] = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                context = browser.new_context(locale="pt-BR", viewport={"width": 1200, "height": 900})
                grid = context.new_page()
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
                return {"complete": covered, "reason": "COVERED" if covered else "PUBLIC_TIMELINE_INCOMPLETE",
                        "items": list(posts.values()), "count": len(posts),
                        "oldest_at": oldest, "newest_at": newest,
                        "grid_count": len(candidates)}
            finally:
                browser.close()
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


def main() -> int:
    # The same OIDC-identified cloud workflow is required for queue mutations.
    client = require_cloud()
    pending = post("instagram-direct-pending", {"limit": 50}, oidc)
    if not pending.get("ok") or pending.get("target_key") != "instagram:universoanthares":
        raise RuntimeError("PUBLIC_RECONCILE_QUEUE_REJECTED")
    jobs = pending.get("items") or []
    eligible = [j for j in jobs if parsed_at(j["publication_started_at"]) >= TAG_CUTOVER]
    if not eligible:
        print(json.dumps({"public_reconcile": "NO_TAGGED_CANDIDATES",
                          "legacy_uncertain_preserved": len(jobs)}), flush=True)
        return 0
    oldest = min(parsed_at(j["publication_started_at"]) for j in eligible)
    public = scan_public_profile(oldest)
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
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"public_reconcile": "FAILED_SAFE",
                          "reason": type(error).__name__}), file=sys.stderr)
        raise SystemExit(2)
