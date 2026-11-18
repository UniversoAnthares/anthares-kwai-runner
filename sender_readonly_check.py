"""Sender.net safe, read-only preflight using a dedicated private token file."""
from __future__ import annotations

import argparse
import json
import os
import stat
from typing import Optional

from sender_marketing import SenderMarketing, SenderAPIError


GATES = ("SENDER_DRAFT_WRITE_ENABLED", "SENDER_LIVE_SEND_ENABLED")


def private_sender_token(filename: str) -> str:
    if not os.path.isabs(filename):
        raise PermissionError("token path must be absolute")
    info = os.stat(filename)
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("Sender token file must have mode 0600")
    if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
        raise PermissionError("Sender token must belong to this runtime account")
    with open(filename, "r", encoding="utf-8") as file:
        token = file.read().strip()
    if not 20 <= len(token) <= 4096 or any(ch.isspace() for ch in token):
        raise ValueError("Sender token is empty or invalid")
    return token


def readiness(client: SenderMarketing) -> dict:
    result = {}
    for label, call in [
        ("groups", client.groups),
        ("campaign_drafts", lambda: client.campaigns(status="DRAFT", limit=1)),
    ]:
        try:
            response = call()
            if not isinstance(response.get("data"), (dict, list)):
                result[label] = "invalid_response"
            else:
                result[label] = "ok"
        except SenderAPIError as exc:
            result[label] = "http_" + str(exc.status)
        except Exception:
            result[label] = "unavailable"
    return {"authenticated": all(value == "ok" for value in result.values()),
            "endpoints": result, "dispatch": "disabled"}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sender API GET-only readiness")
    parser.add_argument("--token-file", required=True)
    options = parser.parse_args(argv)
    if any(os.environ.get(name) == "1" for name in GATES):
        print(json.dumps({"authenticated": False, "error": "write_gate_enabled"}))
        return 3
    try:
        token = private_sender_token(options.token_file)
        result = readiness(SenderMarketing(token=token))
    except (PermissionError, OSError, ValueError):
        print(json.dumps({"authenticated": False, "error": "token_unavailable"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["authenticated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
