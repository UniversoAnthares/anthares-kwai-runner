#!/usr/bin/env python3
"""Reserve, publish and confirm one X/Instagram clip through the durable ledger."""
import argparse
import json
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import confirm, connect, fail, mark_attempt, reserve
from social_adapters.personal_browser import file_sha256, publish


def run(args):
    video = Path(args.video).resolve()
    digest = file_sha256(video)
    if not args.commit:
        return publish(
            args.platform,
            str(video),
            args.caption,
            args.account,
            args.profile,
            commit=False,
        )

    db = connect(args.db)
    reservation = reserve(
        db,
        args.source_id,
        args.start_ms,
        args.end_ms,
        args.platform,
        args.account,
        digest,
    )
    if reservation["already_published"]:
        return {"status": "ALREADY_PUBLISHED", **reservation}
    if not mark_attempt(db, reservation["id"]):
        return {"status": "NOT_ELIGIBLE", **reservation}

    result = publish(
        args.platform,
        str(video),
        args.caption,
        args.account,
        args.profile,
        commit=True,
        headless=not args.headed,
    )
    result["publication_id"] = reservation["id"]

    if result.get("status") == "CONFIRMED":
        evidence = result.get("confirmation_evidence") or {}
        remote_id = str(result.get("remote_id") or "")
        permalink = str(evidence.get("permalink") or "")
        validate_evidence(
            PublicationEvidence(args.platform, args.account, remote_id, permalink),
            args.platform,
            args.account,
        )
        if not confirm(db, reservation["id"], remote_id, permalink):
            raise RuntimeError("ledger rejected confirmed publication")
        result["ledger_status"] = "published"
        return result

    if result.get("status") in {"AUTH_REQUIRED", "IDENTITY_MISMATCH", "FAILED"}:
        fail(db, reservation["id"], retry=True)
        result["ledger_status"] = "retry"
    else:
        fail(db, reservation["id"], retry=False)
        result["ledger_status"] = "uncertain"
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--platform", choices=["x", "instagram"], required=True)
    p.add_argument("--account", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--caption", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--start-ms", type=int, required=True)
    p.add_argument("--end-ms", type=int, required=True)
    p.add_argument("--db", default="state/anthares-publisher.sqlite3")
    p.add_argument("--commit", action="store_true")
    p.add_argument("--headed", action="store_true")
    args = p.parse_args()
    print(json.dumps(run(args), sort_keys=True))


if __name__ == "__main__":
    main()
