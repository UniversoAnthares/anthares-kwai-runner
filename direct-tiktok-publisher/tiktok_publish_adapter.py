#!/usr/bin/env python3
"""Parameterized TikTok publication adapter contract.

This module is intentionally side-effect free: it validates and normalizes a
publication specification, then emits the canonical plan/job/dedupe payloads
consumed by the existing fenced publisher workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ACCOUNT_RE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")
DESTINATIONS = {"tiktok"}


class AdapterSpecError(ValueError):
    pass


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _number_token(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else ("%.3f" % float(value)).rstrip("0").rstrip(".")


@dataclass(frozen=True)
class TikTokPublishSpec:
    account: str
    source_id: str
    source_start: float
    source_end: float
    media_sha256: str
    media_path: str
    destination: str = "tiktok"
    source_url: str = ""
    source_title: str = ""
    title: str = ""
    summary: str = ""
    logical_id: str = ""

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "TikTokPublishSpec":
        try:
            start = float(raw.get("source_start"))
            end = float(raw.get("source_end"))
        except (TypeError, ValueError) as exc:
            raise AdapterSpecError("source_start/source_end must be numeric") from exc
        account = _clean_text(raw.get("account")).lstrip("@").casefold()
        source_id = _clean_text(raw.get("source_id"))
        digest = _clean_text(raw.get("media_sha256")).lower()
        destination = _clean_text(raw.get("destination") or "tiktok").casefold()
        media_path = _clean_text(raw.get("media_path"))
        logical_id = _clean_text(raw.get("logical_id"))
        spec = cls(
            account=account,
            source_id=source_id,
            source_start=start,
            source_end=end,
            media_sha256=digest,
            media_path=media_path,
            destination=destination,
            source_url=_clean_text(raw.get("source_url")),
            source_title=_clean_text(raw.get("source_title")),
            title=_clean_text(raw.get("title")),
            summary=_clean_text(raw.get("summary")),
            logical_id=logical_id,
        )
        spec.validate()
        return spec

    @classmethod
    def from_json_file(cls, path: str | Path) -> "TikTokPublishSpec":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise AdapterSpecError("adapter input must be a JSON object")
        return cls.from_mapping(data)

    @property
    def segment_id(self) -> str:
        return f"{self.source_id}:{_number_token(self.source_start)}:{_number_token(self.source_end)}"

    @property
    def dedupe_key(self) -> str:
        return f"{self.account}::{self.destination}::{self.segment_id}::{self.media_sha256}"

    @property
    def job_id(self) -> str:
        if self.logical_id:
            return self.logical_id
        raw = f"{self.destination}-{self.account}-{self.segment_id}-{self.media_sha256[:12]}"
        safe = re.sub(r"[^A-Za-z0-9._:-]+", "-", raw).strip("-")
        return safe[:180]

    def validate(self) -> None:
        if not ACCOUNT_RE.fullmatch(self.account):
            raise AdapterSpecError("invalid account")
        if not self.source_id or len(self.source_id) > 200:
            raise AdapterSpecError("invalid source_id")
        if self.source_start < 0 or self.source_end <= self.source_start:
            raise AdapterSpecError("invalid source interval")
        if self.destination not in DESTINATIONS:
            raise AdapterSpecError("unsupported destination")
        if not SHA256_RE.fullmatch(self.media_sha256):
            raise AdapterSpecError("media_sha256 must be 64 hex characters")
        if not self.media_path:
            raise AdapterSpecError("media_path is required")

    def verify_media(self) -> None:
        path = Path(self.media_path)
        if not path.is_file() or path.stat().st_size <= 0:
            raise AdapterSpecError("media_path does not exist or is empty")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != self.media_sha256:
            raise AdapterSpecError(f"media hash mismatch: {actual}")

    def plan_payload(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "source_id": self.source_id,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "title": self.title,
            "summary": self.summary,
            "media_path": self.media_path,
            "media_sha256": self.media_sha256,
            "destination": self.destination,
            "account": self.account,
            "dedupe_key": self.dedupe_key,
        }

    def job_payload(self, executor: str = "github") -> dict[str, Any]:
        return {
            "id": self.job_id,
            "platform": self.destination,
            "executor": executor,
            "dedupe_key": self.dedupe_key,
            "source_id": self.source_id,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "media_sha256": self.media_sha256,
            "account": self.account,
            "segment_id": self.segment_id,
        }

    def manifest(self) -> dict[str, Any]:
        return {
            "schema": "anthares.tiktok.publish-adapter.v1",
            "spec": asdict(self),
            "segment_id": self.segment_id,
            "dedupe_key": self.dedupe_key,
            "job_id": self.job_id,
            "plan": self.plan_payload(),
            "job": self.job_payload(),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="JSON publication specification")
    parser.add_argument("--verify-media", action="store_true")
    parser.add_argument("--plan-out")
    parser.add_argument("--job-out")
    args = parser.parse_args()
    spec = TikTokPublishSpec.from_json_file(args.spec)
    if args.verify_media:
        spec.verify_media()
    if args.plan_out:
        Path(args.plan_out).write_text(json.dumps(spec.plan_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
    if args.job_out:
        Path(args.job_out).write_text(json.dumps(spec.job_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(spec.manifest(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
