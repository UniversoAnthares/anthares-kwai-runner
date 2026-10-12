#!/usr/bin/env python3
from __future__ import annotations

import json

import instagram_prepare_media as legacy
from anthares_microcut_v2 import run as semantic_microcut


def microcut(path, output):
    report = semantic_microcut(path, output)
    report["shared_engine"] = True
    return report


legacy.microcut = microcut


def main() -> int:
    plan = legacy.prepare()
    print(json.dumps(plan, ensure_ascii=False, separators=(",", ":")))
    return 0 if plan.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
