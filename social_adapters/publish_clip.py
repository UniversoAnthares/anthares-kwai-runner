#!/usr/bin/env python3
"""Reserve, publish and confirm one clip through the durable multi-platform ledger."""
import argparse
import json
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import confirm, connect, fail, mark_attempt, reserve
from social_adapters.personal_browser import file_sha256, publish as publish_personal
from social_adapters.community_browser import canonical_platform, publish as publish_community

PERSONAL_PLATFORMS = frozenset(("x", "instagram", "facebook"))
COMMUNITY_PLATFORMS = frozenset(("discord", "linkedin", "medium", "rumble", "odysee"))


def _publish(args, platform, commit):
    common = dict(
        platform=platform,
        video=str(Path(args.video).resolve()),
        caption=args.caption,
        account=args.account,
        profile=args.profile,
        commit=commit,
    )
    if platform in PERSONAL_PLATFORMS:
        return publish_personal(**common, headless=not args.headed) if commit else publish_personal(**common)
    if platform in COMMUNITY_PLATFORMS:
        return publish_community(
            **common,
            headless=not args.headed,
            destination=args.destination,
            media_url=args.media_url,
            title=args.title,
        ) if commit else publish_community(
            **common,
            destination=args.destination,
            media_url=args.media_url,
            title=args.title,
        )
    raise ValueError("unsupported platform")


def run(args):
    platform = canonical_platform(args.platform)
    video = Path(args.video).resolve()
    digest = file_sha256(video)
    if not args.commit:
        return _publish(args, platform, commit=False)

    db = connect(args.db)
    reservation = reserve(
        db,
        args.source_id,
        args.start_ms,
        args.end_ms,
        platform,
        args.account,
        digest,
    )
    if reservation["already_published"]:
        return {"status": "ALREADY_PUBLISHED", **reservation}
    if not mark_attempt(db, reservation["id"]):
        return {"status": "NOT_ELIGIBLE", **reservation}

    try:
        result = _publish(args, platform, commit=True)
    except Exception:
        fail(db, reservation["id"], retry=True)
        raise
    result["publication_id"] = reservation["id"]

    if result.get("status") == "CONFIRMED":
        evidence = result.get("confirmation_evidence") or {}
        remote_id = str(result.get("remote_id") or "")
        permalink = str(evidence.get("permalink") or "")
        validate_evidence(
            PublicationEvidence(platform, args.account, remote_id, permalink),
            platform,
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
    p.add_argument(
        "--platform",
        choices=["x", "instagram", "facebook", "discord", "linkedin", "medium", "rumble", "odysee", "odyssey"],
        required=True,
    )
    p.add_argument("--account", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--caption", default="")
    p.add_argument("--title", default="")
    p.add_argument("--profile", required=True)
    p.add_argument("--destination", default="", help="Discord channel URL; optional destination/profile URL for other adapters")
    p.add_argument("--media-url", default="", help="Public media URL used by Medium embed/link publication")
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
