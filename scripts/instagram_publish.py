#!/usr/bin/env python3
"""Publish Instagram Reels through the official Instagram Graph API.

The default transport targets Instagram Login (graph.instagram.com). Set
INSTAGRAM_GRAPH_HOST=graph.facebook.com when using the Facebook Login flow.
No access token is ever written to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class InstagramAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class Quota:
    usage: int | None
    total: int | None
    duration: int | None
    raw: dict[str, Any]

    @property
    def remaining(self) -> int | None:
        if self.usage is None or self.total is None:
            return None
        return max(self.total - self.usage, 0)


class InstagramClient:
    def __init__(
        self,
        user_id: str,
        access_token: str,
        api_version: str = "v26.0",
        graph_host: str = "graph.instagram.com",
        timeout: int = 60,
    ) -> None:
        if not user_id:
            raise ValueError("INSTAGRAM_USER_ID is required")
        if not access_token:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN is required")
        self.user_id = user_id
        self.access_token = access_token
        self.api_version = api_version.strip("/")
        self.graph_host = graph_host.replace("https://", "").replace("http://", "").strip("/")
        self.timeout = timeout

    def _url(self, path: str, query: dict[str, Any] | None = None) -> str:
        url = f"https://{self.graph_host}/{self.api_version}/{path.lstrip('/')}"
        if query:
            clean = {k: str(v) for k, v in query.items() if v is not None}
            url += "?" + urllib.parse.urlencode(clean)
        return url

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "Anthares-Instagram-Publisher/1.0",
        }
        if data is not None:
            body = urllib.parse.urlencode(
                {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in data.items() if v is not None}
            ).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        request = urllib.request.Request(
            self._url(path, query), data=body, headers=headers, method=method.upper()
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": {"message": raw or str(exc)}}
            error = payload.get("error", payload)
            message = error.get("error_user_msg") or error.get("message") or str(error)
            code = error.get("code")
            subcode = error.get("error_subcode")
            suffix = "".join(
                part for part in [f" code={code}" if code is not None else "", f" subcode={subcode}" if subcode is not None else ""]
            )
            raise InstagramAPIError(f"Instagram API HTTP {exc.code}:{suffix} {message}") from exc
        except urllib.error.URLError as exc:
            raise InstagramAPIError(f"Instagram API network error: {exc.reason}") from exc

        if isinstance(payload, dict) and payload.get("error"):
            error = payload["error"]
            message = error.get("error_user_msg") or error.get("message") or str(error)
            raise InstagramAPIError(f"Instagram API error: {message}")
        return payload

    def get_quota(self) -> Quota:
        payload = self._request(
            "GET",
            f"{self.user_id}/content_publishing_limit",
            query={"fields": "quota_usage,config"},
        )
        rows = payload.get("data") or []
        row = rows[0] if rows else {}
        config = row.get("config") or {}
        return Quota(
            usage=_as_int(row.get("quota_usage")),
            total=_as_int(config.get("quota_total")),
            duration=_as_int(config.get("quota_duration")),
            raw=payload,
        )

    def create_reel_container(self, video_url: str, caption: str = "", share_to_feed: bool = True) -> str:
        if not video_url.startswith(("https://", "http://")):
            raise ValueError("video_url must be a public HTTP(S) URL")
        payload = self._request(
            "POST",
            f"{self.user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": share_to_feed,
            },
        )
        container_id = str(payload.get("id") or "")
        if not container_id:
            raise InstagramAPIError("Instagram did not return a media container id")
        return container_id

    def container_status(self, container_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            container_id,
            query={"fields": "status_code,status"},
        )

    def wait_until_ready(self, container_id: str, interval: int = 15, attempts: int = 20) -> dict[str, Any]:
        terminal_errors = {"ERROR", "EXPIRED"}
        for attempt in range(1, attempts + 1):
            status = self.container_status(container_id)
            code = str(status.get("status_code") or "").upper()
            if code in {"FINISHED", "PUBLISHED"}:
                return status
            if code in terminal_errors:
                detail = status.get("status") or code
                raise InstagramAPIError(f"Instagram container {container_id} failed: {detail}")
            if attempt < attempts:
                time.sleep(interval)
        raise InstagramAPIError(
            f"Instagram container {container_id} was not ready after {attempts} checks"
        )

    def publish_container(self, container_id: str) -> str:
        payload = self._request(
            "POST",
            f"{self.user_id}/media_publish",
            data={"creation_id": container_id},
        )
        media_id = str(payload.get("id") or "")
        if not media_id:
            raise InstagramAPIError("Instagram did not return a published media id")
        return media_id

    def publish_reel(
        self,
        video_url: str,
        caption: str = "",
        share_to_feed: bool = True,
        poll_interval: int = 15,
        poll_attempts: int = 20,
    ) -> dict[str, Any]:
        quota = self.get_quota()
        if quota.usage is not None and quota.total is not None and quota.usage >= quota.total:
            raise InstagramAPIError(
                f"Instagram publishing quota exhausted ({quota.usage}/{quota.total})"
            )
        container_id = self.create_reel_container(video_url, caption, share_to_feed)
        status = self.wait_until_ready(container_id, poll_interval, poll_attempts)
        media_id = self.publish_container(container_id)
        return {
            "ok": True,
            "media_id": media_id,
            "container_id": container_id,
            "container_status": status.get("status_code"),
            "quota_before_publish": quota_to_dict(quota),
        }


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def quota_to_dict(quota: Quota) -> dict[str, Any]:
    return {
        "usage": quota.usage,
        "total": quota.total,
        "remaining": quota.remaining,
        "duration_seconds": quota.duration,
    }


def client_from_env() -> InstagramClient:
    return InstagramClient(
        user_id=os.getenv("INSTAGRAM_USER_ID", "").strip(),
        access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip(),
        api_version=os.getenv("INSTAGRAM_API_VERSION", "v26.0").strip() or "v26.0",
        graph_host=os.getenv("INSTAGRAM_GRAPH_HOST", "graph.instagram.com").strip() or "graph.instagram.com",
        timeout=int(os.getenv("INSTAGRAM_HTTP_TIMEOUT", "60")),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Anthares official Instagram publisher")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("quota", help="Print live content publishing quota")

    publish = sub.add_parser("publish-reel", help="Publish one Reel")
    publish.add_argument("--video-url", required=True)
    publish.add_argument("--caption", default="")
    publish.add_argument("--share-to-feed", action=argparse.BooleanOptionalAction, default=True)
    publish.add_argument("--poll-interval", type=int, default=15)
    publish.add_argument("--poll-attempts", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        client = client_from_env()
        if args.command == "quota":
            result = {"ok": True, "quota": quota_to_dict(client.get_quota())}
        else:
            result = client.publish_reel(
                video_url=args.video_url,
                caption=args.caption,
                share_to_feed=args.share_to_feed,
                poll_interval=args.poll_interval,
                poll_attempts=args.poll_attempts,
            )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (InstagramAPIError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
