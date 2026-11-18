"""Read-only campaign operations and local suppression reconciliation.

All Brevo calls here are GET; local records are private SQLite and monotonic.
This program never sends, creates contacts, schedules or edits campaigns.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from brevo_marketing import BrevoMarketing, BrevoAPIError, _email, _positive_id
from brevo_readonly_check import key_from_private_file


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SuppressionLedger:
    """Sticky global suppressions; never silently re-enable an address."""

    def __init__(self, db_path: str):
        self.path = db_path
        if os.path.exists(db_path) and os.path.islink(db_path):
            raise PermissionError("suppression db may not be a symlink")
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS brevo_suppressions(
                email TEXT PRIMARY KEY, reason TEXT NOT NULL,
                first_seen TEXT NOT NULL, last_seen TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS brevo_sync_runs(
                id INTEGER PRIMARY KEY, checked_at TEXT NOT NULL,
                contacts_checked INTEGER NOT NULL,
                suppressed_seen INTEGER NOT NULL,
                missing_list_status INTEGER NOT NULL
            )""")

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        if os.path.isfile(self.path):
            os.chmod(self.path, 0o600)
        return conn

    def is_suppressed(self, email: str) -> bool:
        with self._connect() as conn:
            return conn.execute(
                "SELECT 1 FROM brevo_suppressions WHERE email=?",
                (_email(email),)).fetchone() is not None

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM brevo_suppressions").fetchone()[0]

    def fresh_lookup(self, max_age_minutes: int = 60):
        """Require a recent complete Brevo scan for every live campaign dispatch."""
        with self._connect() as conn:
            row = conn.execute("""SELECT checked_at, missing_list_status
                FROM brevo_sync_runs ORDER BY id DESC LIMIT 1""").fetchone()
        if row is None or row[1] != 0:
            raise PermissionError("Brevo suppression sync is incomplete")
        try:
            timestamp = datetime.fromisoformat(row[0])
        except (ValueError, TypeError):
            raise PermissionError("invalid suppression checkpoint") from None
        age = datetime.now(timezone.utc) - timestamp
        if not timedelta(0) <= age <= timedelta(minutes=max_age_minutes):
            raise PermissionError("Brevo suppression sync is stale")
        return self.is_suppressed

    def save_snapshot(self, suppressed: dict[str, str], checked: int,
                      missing_list_status: int) -> dict:
        if checked < len(suppressed) or missing_list_status < 0:
            raise ValueError("invalid suppression snapshot counts")
        now = utcnow()
        with self._connect() as conn:
            for email, reason in suppressed.items():
                if reason not in {"brevo_global_blacklist", "brevo_list_unsubscribed"}:
                    raise ValueError("invalid suppression reason")
                conn.execute("""INSERT INTO brevo_suppressions(email,reason,first_seen,last_seen)
                    VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET last_seen=excluded.last_seen""",
                    (_email(email), reason, now, now))
            conn.execute("""INSERT INTO brevo_sync_runs(
                checked_at,contacts_checked,suppressed_seen,missing_list_status)
                VALUES(?,?,?,?)""", (now, checked, len(suppressed), missing_list_status))
        return {"contacts_checked": checked, "suppressed_seen": len(suppressed),
                "sticky_suppressions": self.count(),
                "missing_list_status": missing_list_status}


def pull_brevo_suppressions(client: BrevoMarketing, ledger: SuppressionLedger,
                            max_contacts: int = 50000) -> dict:
    """Reconcile global blacklist and per-list opt-outs before writing any state.

    Brevo's account-wide contact endpoint may return null/omitted unsubscribe
    metadata. Confirm that metadata through the list-scoped endpoint instead.
    """
    size = 500
    offset = 0
    collected: dict[str, str] = {}
    expected = None
    unresolved: dict[str, set[int]] = {}
    list_ids: set[int] = set()
    while True:
        response = client._request("GET", f"/contacts?limit={size}&offset={offset}")
        contacts = response.get("contacts")
        count = response.get("count")
        if (not isinstance(contacts, list) or not isinstance(count, int)
                or isinstance(count, bool) or count < 0 or count > max_contacts):
            raise RuntimeError("unexpected or excessive Brevo contacts response")
        if expected is None:
            expected = count
        if count != expected or len(contacts) > size or offset + len(contacts) > max_contacts:
            raise RuntimeError("contacts changed during paginated reconciliation")
        for contact in contacts:
            if not isinstance(contact, dict):
                raise RuntimeError("invalid Brevo contact record")
            email = contact.get("email")
            if not email:
                continue
            normalized = _email(email)
            if not isinstance(contact.get("emailBlacklisted"), bool):
                raise RuntimeError("missing global email blacklist status")
            memberships = contact.get("listIds") or []
            if not isinstance(memberships, list):
                raise RuntimeError("invalid list memberships")
            ids = {_positive_id(item, "listId") for item in memberships}
            list_ids.update(ids)
            unsubscribed = contact.get("listUnsubscribed")
            if unsubscribed is None and ids:
                unresolved[normalized] = set(ids)
            elif unsubscribed is not None:
                if not isinstance(unsubscribed, list):
                    raise RuntimeError("invalid unsubscribe status")
                if unsubscribed:
                    collected[normalized] = "brevo_list_unsubscribed"
            if contact["emailBlacklisted"]:
                collected[normalized] = "brevo_global_blacklist"
        offset += len(contacts)
        if offset >= expected:
            break
        if not contacts:
            raise RuntimeError("premature end of contact scan")

    if len(list_ids) > 100:
        raise RuntimeError("too many contact lists for one safe reconciliation")
    # List-specific GET responses are authoritative for unsubscribe membership.
    for list_id in sorted(list_ids):
        list_offset = 0
        list_expected = None
        while True:
            result = client._request(
                "GET", f"/contacts/lists/{list_id}/contacts?limit={size}&offset={list_offset}")
            members = result.get("contacts")
            count = result.get("count")
            if (not isinstance(members, list) or not isinstance(count, int)
                    or count < 0 or count > max_contacts or len(members) > size):
                raise RuntimeError("invalid Brevo list scan")
            if list_expected is None:
                list_expected = count
            if count != list_expected or list_offset + len(members) > max_contacts:
                raise RuntimeError("contact list changed during reconciliation")
            for member in members:
                if not isinstance(member, dict) or not member.get("email"):
                    raise RuntimeError("invalid list member")
                address = _email(member["email"])
                ids = member.get("listIds") or []
                if list_id not in ids or not isinstance(member.get("emailBlacklisted"), bool):
                    raise RuntimeError("list member status is inconsistent")
                unsubscribed = member.get("listUnsubscribed")
                if not isinstance(unsubscribed, list):
                    raise RuntimeError("list opt-out status is unavailable")
                if member["emailBlacklisted"]:
                    collected[address] = "brevo_global_blacklist"
                elif list_id in unsubscribed:
                    collected.setdefault(address, "brevo_list_unsubscribed")
                if address in unresolved:
                    unresolved[address].discard(list_id)
                    if not unresolved[address]:
                        del unresolved[address]
            list_offset += len(members)
            if list_offset >= list_expected:
                break
            if not members:
                raise RuntimeError("premature end of list scan")
    if unresolved:
        raise RuntimeError("one or more unsubscribe states could not be verified")
    return ledger.save_snapshot(collected, offset, 0)


def safe_campaign_report(client: BrevoMarketing, campaign_id: int) -> dict:
    """Sanitize report: no HTML, addresses, links or recipients appear in output."""
    cid = _positive_id(campaign_id, "campaign_id")
    report = client._request(
        "GET", f"/emailCampaigns/{cid}?statistics=globalStats&excludeHtmlContent=true")
    if not isinstance(report, dict) or report.get("id") != cid:
        raise RuntimeError("campaign id differs from requested report")
    statistics = report.get("statistics", {})
    global_stats = statistics.get("globalStats", {}) if isinstance(statistics, dict) else {}
    allowed = {"sent", "delivered", "hardBounces", "softBounces", "complaints",
               "unsubscriptions", "uniqueClicks", "uniqueViews", "viewed", "clickers"}
    numbers = {key: value for key, value in global_stats.items()
               if key in allowed and type(value) in {int, float}}
    return {"campaign_id": cid, "status": report.get("status", "unknown"),
            "statistics": numbers, "test_sent": bool(report.get("testSent"))}


def safe_status(client: BrevoMarketing, ledger: SuppressionLedger) -> dict:
    account = client.account_info()
    lists = client.lists(limit=50)
    drafts = client.campaigns(status="draft", limit=1)
    if not all(isinstance(x, dict) for x in (account, lists, drafts)):
        raise RuntimeError("invalid Brevo account response")
    allowed_lists = [
        {"id": int(row["id"]), "known_subscribers": int(row["uniqueSubscribers"]) if
         isinstance(row.get("uniqueSubscribers"), int) else None}
        for row in lists.get("lists", [])
        if isinstance(row, dict) and "id" in row
    ]
    return {"api": "connected", "lists": allowed_lists,
            "list_count": lists.get("count"),
            "draft_count": drafts.get("count"),
            "local_sticky_suppressions": ledger.count(),
            "mailing": "approval_required",
            "sending_enabled": False}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Anthares Brevo SSH operator: read-only")
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--db", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("sync-suppressions")
    report_parser = sub.add_parser("campaign-report")
    report_parser.add_argument("--campaign-id", required=True, type=int)
    args = parser.parse_args(argv)
    gates = ("BREVO_LIVE_SEND_ENABLED", "BREVO_DRAFT_WRITE_ENABLED",
             "BREVO_CONTACT_SYNC_ENABLED", "BREVO_TEST_SEND_ENABLED")
    if any(os.environ.get(gate) == "1" for gate in gates):
        print(json.dumps({"ok": False, "error": "write_gate_enabled"}))
        return 3
    try:
        key = key_from_private_file(args.key_file)
        client = BrevoMarketing(api_key=key)
        ledger = SuppressionLedger(args.db)
        if args.command == "status":
            result = safe_status(client, ledger)
        elif args.command == "sync-suppressions":
            result = pull_brevo_suppressions(client, ledger)
        else:
            result = safe_campaign_report(client, args.campaign_id)
    except BrevoAPIError as e:
        print(json.dumps({"ok": False, "http_code": e.status}))
        return 1
    except (ValueError, RuntimeError, PermissionError, OSError):
        print(json.dumps({"ok": False, "error": "operation_failed"}))
        return 2
    print(json.dumps({"ok": True, "result": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
