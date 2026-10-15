#!/usr/bin/env python3
"""Execute the canonical TikTok publisher from a validated adapter spec.

Queue/lease/fence/reconciliation remain control-plane responsibilities. This
module replaces the old one-shot-specific plan construction with one reusable
parameterized adapter boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from tiktok_publish_adapter import TikTokPublishSpec


def prepare(spec_path: str, plan_path: str) -> TikTokPublishSpec:
    spec = TikTokPublishSpec.from_json_file(spec_path)
    spec.verify_media()
    target = Path(plan_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec.plan_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
    return spec


def execute(spec_path: str, plan_path: str, publisher: str | None = None) -> int:
    spec = prepare(spec_path, plan_path)
    env = os.environ.copy()
    env["EXPECTED_TIKTOK_USERNAME"] = spec.account
    env["TIKTOK_YOUTUBE_PLAN"] = str(Path(plan_path).resolve())
    script = Path(publisher) if publisher else Path(__file__).with_name("tiktok_cloud_publish.py")
    result = subprocess.run([sys.executable, str(script)], cwd=str(script.parent), env=env, check=False)
    return int(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="JSON TikTokPublishSpec")
    parser.add_argument("--plan", default=os.getenv("TIKTOK_YOUTUBE_PLAN", "/tmp/tiktok-plan.json"))
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    spec = prepare(args.spec, args.plan)
    print("TIKTOK_ADAPTER_READY=" + json.dumps({
        "job_id": spec.job_id,
        "dedupe_key": spec.dedupe_key,
        "account": spec.account,
        "destination": spec.destination,
        "segment_id": spec.segment_id,
    }, sort_keys=True), flush=True)
    if args.prepare_only:
        return 0
    return execute(args.spec, args.plan)


if __name__ == "__main__":
    raise SystemExit(main())
