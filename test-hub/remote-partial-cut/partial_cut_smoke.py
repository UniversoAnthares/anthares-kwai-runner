#!/usr/bin/env python3
"""Real media smoke: partial YouTube transfer + remote microcut processing.

No social publication and no full-download fallback. The source is requested only
for a bounded section. A small interior interval is then removed to prove a
second remote processing stage over the partial media.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

VIDEO_ID = os.environ.get("TEST_YOUTUBE_VIDEO_ID", "b6gL9plY_6w").strip()
SECTION_START = float(os.environ.get("TEST_SECTION_START", "60"))
SECTION_END = float(os.environ.get("TEST_SECTION_END", "150"))
ROOT = pathlib.Path("test-output")
ROOT.mkdir(exist_ok=True)
PARTIAL_TMPL = str(ROOT / "partial.%(ext)s")
FINAL = ROOT / "partial-microcut.mp4"
MANIFEST = ROOT / "manifest.json"
URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def run(*args: str, capture: bool = False) -> str:
    p = subprocess.run(args, check=True, text=True, capture_output=capture)
    return (p.stdout or "").strip() if capture else ""


def probe(path: pathlib.Path) -> dict:
    raw = run(
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "json", str(path), capture=True,
    )
    return json.loads(raw)["format"]


def main() -> int:
    if not VIDEO_ID:
        raise RuntimeError("missing video id")
    if SECTION_START < 0 or SECTION_END <= SECTION_START:
        raise RuntimeError("invalid bounded section")

    meta_raw = run(
        sys.executable, "-m", "yt_dlp", "--skip-download", "--no-playlist",
        "--dump-single-json", URL, capture=True,
    )
    meta = json.loads(meta_raw)
    source_duration = float(meta.get("duration") or 0)
    requested_duration = SECTION_END - SECTION_START
    if source_duration and SECTION_END >= source_duration:
        raise RuntimeError(
            f"test section exceeds source: section_end={SECTION_END} source={source_duration}"
        )

    # PRIMARY MECHANISM: yt-dlp resolves the authenticated/ephemeral YouTube
    # media URLs; ffmpeg seeks only the requested interval. This is deliberately
    # bounded and has no code path that downloads the full source.
    run(
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",
        "--download-sections", f"*{SECTION_START}-{SECTION_END}",
        "--force-keyframes-at-cuts",
        "--merge-output-format", "mp4",
        "-f", "bv*[height<=720]+ba/b[height<=720]/b",
        "-o", PARTIAL_TMPL,
        URL,
    )
    candidates = sorted(ROOT.glob("partial.*"))
    candidates = [p for p in candidates if p.name != FINAL.name]
    if not candidates:
        raise RuntimeError("partial media was not produced")
    partial = max(candidates, key=lambda p: p.stat().st_size)
    partial_probe = probe(partial)
    partial_duration = float(partial_probe["duration"])

    # SECOND STAGE (remote processing): remove a 3-second interior interval,
    # analogous to one semantic microcut. This smoke validates media plumbing;
    # production semantic boundaries remain AI-selected by the CORTES pipeline.
    keep1_end = min(35.0, max(5.0, partial_duration / 2 - 2.0))
    keep2_start = min(keep1_end + 3.0, partial_duration - 5.0)
    if keep2_start <= keep1_end or partial_duration < 20:
        raise RuntimeError(f"partial section unexpectedly short: {partial_duration}")
    vf = (
        f"[0:v]trim=start=0:end={keep1_end},setpts=PTS-STARTPTS[v0];"
        f"[0:a]atrim=start=0:end={keep1_end},asetpts=PTS-STARTPTS[a0];"
        f"[0:v]trim=start={keep2_start}:end={partial_duration},setpts=PTS-STARTPTS[v1];"
        f"[0:a]atrim=start={keep2_start}:end={partial_duration},asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    )
    run(
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(partial),
        "-filter_complex", vf, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-movflags", "+faststart", str(FINAL),
    )
    final_probe = probe(FINAL)

    result = {
        "ok": True,
        "video_id": VIDEO_ID,
        "source_url": URL,
        "source_duration_seconds": source_duration,
        "requested_section": [SECTION_START, SECTION_END],
        "requested_duration_seconds": requested_duration,
        "partial_file": partial.name,
        "partial_size_bytes": partial.stat().st_size,
        "partial_duration_seconds": partial_duration,
        "microcut_removed_seconds": round(keep2_start - keep1_end, 3),
        "final_file": FINAL.name,
        "final_size_bytes": FINAL.stat().st_size,
        "final_duration_seconds": float(final_probe["duration"]),
        "remote_processing": "github_hosted_runner",
        "full_source_download_requested": False,
        "full_download_fallback": "PENDING_NEXT_ROUND",
        "social_publish": False,
    }
    MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PARTIAL_CUT_SMOKE_OK " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
