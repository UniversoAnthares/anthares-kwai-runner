"""Credential-safe GET-only Resend marketing readiness probe."""
from __future__ import annotations

import argparse
import json
import os
import stat
from typing import Optional

from resend_marketing import ResendMarketing, ResendMarketingError


def private_api_key(path: str) -> str:
    if not os.path.isabs(path):
        raise PermissionError("API key file path must be absolute")
    info = os.stat(path)
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("API key file must be private")
    if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
        raise PermissionError("API key file ownership mismatch")
    with open(path, "r", encoding="utf-8") as f:
        key = f.read().strip()
    if not key.startswith("re_") or len(key) < 20 or any(c.isspace() for c in key):
        raise ValueError("Resend API key missing or invalid")
    return key


def read_only_status(client: ResendMarketing) -> dict:
    status = {}
    for label, action in [("segments", client.segments),
                          ("broadcasts", client.broadcasts)]:
        try:
            result = action()
            status[label] = "ok" if isinstance(result.get("data"), list) else "bad_response"
        except ResendMarketingError as exc:
            status[label] = "http_" + str(exc.status)
        except Exception:
            status[label] = "unavailable"
    return {"authenticated": all(v == "ok" for v in status.values()),
            "resources": status, "mailing_dispatch": "disabled"}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Resend marketing API GET-only diagnostic")
    parser.add_argument("--key-file", required=True)
    args = parser.parse_args(argv)
    if any(os.environ.get(flag) == "1" for flag in
           ("RESEND_DRAFT_WRITE_ENABLED", "RESEND_LIVE_SEND_ENABLED")):
        print(json.dumps({"authenticated": False, "error": "mutating_gate_enabled"}))
        return 3
    try:
        client = ResendMarketing(api_key=private_api_key(args.key_file))
        status = read_only_status(client)
    except (PermissionError, ValueError, OSError):
        print(json.dumps({"authenticated": False, "error": "private_key_unavailable"}))
        return 2
    print(json.dumps(status, sort_keys=True))
    return 0 if status["authenticated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
