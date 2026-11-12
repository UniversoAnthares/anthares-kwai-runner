"""Read-only public-profile + source-media reconciliation of a Kwai uncertain cut.

Arguments are the exact canonical CORTES job and its authorized source URL.
Returns machine-readable evidence to stdout, never changes queue states.
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(job_id: str, source_url: str, account: str) -> int:
    if account not in ("lucasrosalem", "universoanthares"):
        raise ValueError("account_not_allowed")
    if not job_id.startswith("kwai-cortes-"):
        raise ValueError("job_id_invalid")
    if not source_url.startswith("https://anthares.us/wp-content/uploads/anthares-clips/"):
        raise ValueError("source_url_not_allowed")
    os.environ["KWAI_EXPECTED_ACCOUNT"] = account
    from kwai_public_feed_proof import prove, scan_public_profile_window
    state_file = ROOT / ".state" / "kwai-native-cortes" / (job_id + ".json")
    state = json.loads(state_file.read_text(encoding="utf8"))
    if state.get("job_id") not in (None, job_id):
        raise ValueError("state_job_mismatch")
    if state.get("publication_attempted") is not True or not state.get("media_sha256"):
        raise ValueError("source_state_unverifiable")
    evidence_dir = ROOT / ".state" / "kwai-memu-evidence" / job_id
    base_file = evidence_dir / "public-feed-baseline.json"
    baseline = json.loads(base_file.read_text(encoding="utf8")).get("photo_ids", []) if base_file.exists() else []
    try:
        result = prove(
            job_id=job_id, caption=state["caption"],
            expected_sha=state["media_sha256"], source_url=source_url,
            started_ms=int(state["publication_attempted_at"])*1000,
            baseline_ids=baseline,
        )
    except Exception as exc:
        print(json.dumps({"status": "MEDIA_PROOF_PENDING", "job_id": job_id,
              "error_kind": type(exc).__name__, "error": str(exc)[:200]}, ensure_ascii=False))
        return 2
    print(json.dumps({
        "status": "VERIFIED_PUBLIC_MEDIA", "job_id": job_id,
        "account": account, "photo_id": result["photo_id"],
        "public_url": result["public_url"],
        "source_sha256": result["media_sha256"],
        "public_sha256": result["public_media_sha256"],
        "caption_match": result["title_match"],
        "posted_ms": result["public_post_timestamp_ms"],
        "qualifying_frames": result["media_match"]["qualifying_distinct_frames"],
        "inliers": result["media_match"]["source_best_inliers"],
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--job-id", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--account", required=True, choices=("lucasrosalem", "universoanthares"))
    a = p.parse_args()
    return run(a.job_id, a.source_url, a.account)

if __name__ == "__main__":
    sys.exit(main())
