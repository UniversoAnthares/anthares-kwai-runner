"""One-way, GET-only sync of Resend's global suppression list into a private queue.

Never deletes source contacts. Reconciliation preserves an audit record and
prevents resends to bounced, complained-about or manually suppressed addresses.
"""
from __future__ import annotations
import argparse
import json
import os
import stat
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from pastor_mailing_queue import PastoralQueue, normalize_address

ROOT = "https://api.resend.com"
REASON = {"bounce": "hard_bounce", "complaint": "complaint", "manual": "manual_block"}


def read_key(path: str) -> str:
    p = Path(path)
    s = p.stat()
    if not p.is_absolute() or not stat.S_ISREG(s.st_mode) or s.st_mode & 0o077:
        raise PermissionError("API key must be private")
    if hasattr(os, "geteuid") and s.st_uid != os.geteuid():
        raise PermissionError("API key owner mismatch")
    key = p.read_text().strip()
    if not key.startswith("re_") or len(key) < 20:
        raise ValueError("Resend API key unavailable")
    return key


def fetch_suppressions(key: str, transport: Callable[[str], dict] | None = None) -> list[dict]:
    """Fetch complete list before applying changes; fail closed on missing pages."""
    def live(path: str) -> dict:
        req = urllib.request.Request(ROOT + path,
            headers={"Authorization": "Bearer " + key,
                     "User-Agent": "anthares-mailing/1.0",
                     "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)

    call = transport or live
    records = []
    observed = set()
    cursor = None
    for _ in range(300):
        route = "/suppressions?limit=100"
        if cursor:
            route += "&after=" + urllib.parse.quote(cursor, safe="")
        page = call(route)
        if (not isinstance(page, dict) or not isinstance(page.get("data"), list) or
                not isinstance(page.get("has_more"), bool)):
            raise RuntimeError("unverified suppression pagination")
        items = page["data"]
        if len(items) > 100 or page["has_more"] and not items:
            raise RuntimeError("invalid page length")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise RuntimeError("invalid suppression ID")
            ident = item["id"]
            if ident in observed:
                raise RuntimeError("duplicate cursor")
            observed.add(ident)
            address = normalize_address(item.get("email",""))
            origin = item.get("origin")
            if origin not in REASON:
                raise RuntimeError("unknown suppression origin")
            records.append({"id": ident, "email": address, "origin": origin})
        if not page["has_more"]:
            return records
        cursor = items[-1]["id"]
    raise RuntimeError("suppression pages exceed cap")


def sync(queue: PastoralQueue, items: list[dict]) -> dict:
    total, already, unknown, newly = len(items), 0, 0, 0
    with queue.connect() as db:
        contacts = {r[0] for r in db.execute("SELECT email FROM contacts")}
        old = {r[0] for r in db.execute("SELECT email FROM suppressions")}
    for item in items:
        email = item["email"]
        if email not in contacts:
            unknown += 1
            continue
        if email in old:
            already += 1
            continue
        newly += int(queue.suppress(email, REASON[item["origin"]],
                         "resend-suppression:" + item["id"]))
        old.add(email)
    return {"provider_suppressions":total, "newly_suppressed":newly,
            "previously_suppressed":already, "outside_local_queue":unknown,
            "mailing_send_enabled":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",required=True)
    parser.add_argument("--key-file",required=True)
    args=parser.parse_args()
    queue=PastoralQueue(args.db)
    items=fetch_suppressions(read_key(args.key_file))
    print(json.dumps(sync(queue,items),sort_keys=True))


if __name__ == "__main__":
    main()
