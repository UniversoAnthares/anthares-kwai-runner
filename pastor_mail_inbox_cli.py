"""Minimal CLI to dedupe processed Hostinger inbox message UIDs.

Mark UIDs only AFTER the digest email send is confirmed. Does not read email,
open provider credentials or initiate any outbound send.
"""
import argparse
import json
import re
from datetime import datetime, timezone

from pastor_mailing_queue import PastoralQueue

MAILBOX = "contato@anthares.us"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    modes = p.add_subparsers(dest="action", required=True)
    modes.add_parser("list")
    mark = modes.add_parser("mark")
    mark.add_argument("--uid", required=True)
    mark.add_argument("--kind", required=True, choices=[
        "reply", "hard_bounce", "soft_bounce", "complaint", "unsubscribe", "other"])
    mark.add_argument("--received-at", required=True)
    args = p.parse_args()
    queue = PastoralQueue(args.db)
    if args.action == "list":
        with queue.connect() as db:
            rows = db.execute(
                "SELECT provider_uid FROM inbound_events WHERE mailbox=? ORDER BY CAST(provider_uid AS INTEGER)",
                (MAILBOX,)).fetchall()
        print(json.dumps({"processed_uids": [r[0] for r in rows]}))
        return
    if not re.fullmatch(r"[1-9][0-9]{0,17}", args.uid):
        raise ValueError("invalid Hostinger INBOX UID")
    moment = datetime.fromisoformat(args.received_at.replace("Z","+00:00"))
    if moment.tzinfo is None or moment > datetime.now(timezone.utc):
        raise ValueError("received time invalid")
    created = queue.record_inbox_event(MAILBOX, args.uid, args.kind, "", "",
                                      moment.isoformat())
    print(json.dumps({"uid":args.uid,"newly_marked":created}))


if __name__ == "__main__":
    main()
