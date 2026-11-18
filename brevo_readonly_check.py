"""Read-only Brevo health check using a private API-key file.

Requires Python 3.11+, a key file mode 0600, and explicit --key-file. It never
logs the key, response payloads, account identity, lists, or contacts.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
from typing import Optional

from brevo_marketing import BrevoMarketing, BrevoAPIError


def key_from_private_file(path: str) -> str:
    if not os.path.isabs(path):
        raise PermissionError("key path must be absolute")
    info = os.stat(path)  # follow the private state/secret symlink
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("key file must be private (mode 600)")
    if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
        raise PermissionError("key file must belong to this runtime account")
    with open(path, "r", encoding="utf-8") as handle:
        key = handle.read().strip()
    if not key.startswith("xkeysib-") or len(key) < 30:
        raise ValueError("invalid Brevo key format")
    return key


def read_only_status(client: BrevoMarketing) -> dict:
    result = {}
    for name, action in [
        ("account", client.account_info),
        ("lists", lambda: client.lists(limit=1)),
        ("campaigns", lambda: client.campaigns(status="draft", limit=1)),
    ]:
        try:
            payload = action()
            result[name] = "ok" if isinstance(payload, dict) else "invalid_response"
        except BrevoAPIError as exc:
            result[name] = "http_" + str(exc.status)
        except Exception:
            result[name] = "unavailable"
    return {"authenticated": all(v == "ok" for v in result.values()),
            "read_endpoints": result, "sending": "disabled"}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Brevo API read-only probe")
    parser.add_argument("--key-file", required=True)
    args = parser.parse_args(argv)

    # Refuse to execute a health probe with any mutating operation enabled.
    gate_names = (
        "BREVO_LIVE_SEND_ENABLED", "BREVO_DRAFT_WRITE_ENABLED",
        "BREVO_CONTACT_SYNC_ENABLED", "BREVO_TEST_SEND_ENABLED",
    )
    if any(os.environ.get(name) == "1" for name in gate_names):
        print(json.dumps({"authenticated": False, "error": "write_gate_enabled"}))
        return 3
    try:
        key = key_from_private_file(args.key_file)
        client = BrevoMarketing(api_key=key)
        outcome = read_only_status(client)
    except (OSError, ValueError, PermissionError):
        print(json.dumps({"authenticated": False, "error": "credential_unavailable"}))
        return 2
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["authenticated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
