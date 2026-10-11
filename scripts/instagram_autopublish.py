#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from instagram_publish import InstagramAPIError, client_from_env

WP_MEDIA_ENDPOINT = os.getenv(
    "INSTAGRAM_WP_MEDIA_ENDPOINT",
    "https://anthares.us/wp-json/wp/v2/media?media_type=video&per_page=100&orderby=date&order=desc",
).strip()
LEDGER_PATH = Path(os.getenv("INSTAGRAM_LEDGER", ".state/instagram-published.json"))
MICROCUT_MARKER = os.getenv("INSTAGRAM_MICROCUT_MARKER", "-microcut").strip()


def _request_json(url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "Anthares-Instagram-Scheduler/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_media() -> list[dict[str, Any]]:
    payload = _request_json(WP_MEDIA_ENDPOINT)
    if not isinstance(payload, list):
        raise RuntimeError("WordPress media endpoint did not return a list")
    return [row for row in payload if isinstance(row, dict)]


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"version": 1, "published": {}}
    if not isinstance(data, dict):
        data = {"version": 1, "published": {}}
    if not isinstance(data.get("published"), dict):
        data["published"] = {}
    data.setdefault("version", 1)
    return data


def save_ledger(data: dict[str, Any], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _source_url(row: dict[str, Any]) -> str:
    return str(row.get("source_url") or "").strip()


def is_eligible(row: dict[str, Any], allow_legacy: bool = False) -> bool:
    url = _source_url(row)
    if not url.startswith(("https://", "http://")):
        return False
    lower = url.lower()
    if "/anthares-clips/" not in lower or not lower.split("?", 1)[0].endswith(".mp4"):
        return False
    if allow_legacy:
        return True
    return bool(MICROCUT_MARKER and MICROCUT_MARKER.casefold() in lower.casefold())


def select_next(rows: list[dict[str, Any]], ledger: dict[str, Any], allow_legacy: bool = False) -> dict[str, Any] | None:
    published = ledger.get("published") or {}
    for row in rows:
        if not is_eligible(row, allow_legacy=allow_legacy):
            continue
        media_id = str(row.get("id") or "")
        url = _source_url(row)
        if media_id and media_id in published:
            continue
        if any(isinstance(v, dict) and str(v.get("source_url") or "") == url for v in published.values()):
            continue
        return row
    return None


def clean_caption(row: dict[str, Any]) -> str:
    title = row.get("title")
    if isinstance(title, dict):
        title = title.get("rendered")
    text = html.unescape(str(title or "")).strip()
    if not text:
        text = Path(_source_url(row).split("?", 1)[0]).stem
    text = re.sub(r"^live_[A-Za-z0-9_-]+?_[0-9]{1,3}_", "", text, flags=re.I)
    text = re.sub(r"-microcut(?:-creative)?$", "", text, flags=re.I)
    text = re.sub(r"[_-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    if text:
        text = text[0].upper() + text[1:]
    suffix = " #literatura #escrita #UniversoAnthares"
    room = max(0, 2200 - len(suffix))
    return text[:room].rstrip() + suffix


def publish_next(*, allow_legacy: bool = False, dry_run: bool = False) -> dict[str, Any]:
    ledger = load_ledger()
    row = select_next(fetch_media(), ledger, allow_legacy=allow_legacy)
    if row is None:
        return {"ok": True, "published": False, "reason": "no_eligible_media"}

    source_url = _source_url(row)
    caption = clean_caption(row)
    media_key = str(row.get("id") or source_url)
    if dry_run:
        return {
            "ok": True,
            "published": False,
            "dry_run": True,
            "source_attachment_id": str(row.get("id") or ""),
            "source_url": source_url,
            "caption": caption,
        }

    result = client_from_env().publish_reel(source_url, caption=caption, share_to_feed=True)
    record = {
        "source_attachment_id": str(row.get("id") or ""),
        "source_url": source_url,
        "instagram_media_id": str(result.get("media_id") or ""),
        "published_at": int(time.time()),
        "caption": caption,
        "quota_before_publish": result.get("quota_before_publish"),
    }
    ledger["published"][media_key] = record
    save_ledger(ledger)
    return {
        "ok": True,
        "published": True,
        "source_attachment_id": record["source_attachment_id"],
        "source_url": source_url,
        "instagram_media_id": record["instagram_media_id"],
        "quota_before_publish": record["quota_before_publish"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish the next Anthares microcut to Instagram")
    parser.add_argument("--allow-legacy", action="store_true", help="Permit pre-microcut Anthares clips")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        print(json.dumps(publish_next(allow_legacy=args.allow_legacy, dry_run=args.dry_run), ensure_ascii=False))
        return 0
    except (InstagramAPIError, RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
