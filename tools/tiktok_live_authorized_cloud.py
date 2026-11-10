#!/usr/bin/env python3
"""Cloud-only, authorized TikTok ingest adapter for *disclosed prerecorded* Anthares programming.

Fails closed without an explicit TikTok-provided RTMPS destination and an operator
authorization gate. Never starts a LIVE room, guesses an ingest key, or impersonates
live interactions. No local desktop/Android dependency.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit

DEFAULT_SOURCE = "https://anthares.us/wp-content/uploads/anthares-live-static/live.m3u8"
MAX_SECONDS = 6 * 3600

def validate_source(source):
    u = urlsplit(source)
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        raise ValueError("source_must_be_https")
    return source

def validate_destination(destination):
    if not destination:
        raise ValueError("tiktok_rtmp_not_authorized")
    u = urlsplit(destination)
    if u.scheme not in ("rtmps", "rtmp") or not u.hostname or not u.path.strip("/"):
        raise ValueError("tiktok_ingest_invalid")
    if u.username or u.password:
        raise ValueError("tiktok_ingest_credentials_in_authority")
    return destination

def source_preflight(source):
    req = urllib.request.Request(source, headers={"User-Agent": "Anthares-Live-Preflight/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        data = response.read(4096)
        if response.status != 200 or b"#EXTM3U" not in data:
            raise RuntimeError("hls_manifest_unavailable")
    return True

def build_command(source, destination, seconds):
    # No attempt to conceal recorded content: the identification remains on screen.
    vf = (
        "scale=720:1280:force_original_aspect_ratio=decrease,"
        "pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,"
        "drawbox=x=0:y=0:w=iw:h=72:color=black@0.85:t=fill,"
        "drawtext=text='PROGRAMA GRAVADO':fontsize=27:fontcolor=white:"
        "x=(w-text_w)/2:y=20"
    )
    return [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
        "-re", "-i", source, "-t", str(seconds),
        "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-r", "30", "-g", "60",
        "-b:v", "2000k", "-maxrate", "2300k", "-bufsize", "4600k",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", destination
    ]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preflight", action="store_true")
    p.add_argument("--seconds", type=int, default=600)
    args = p.parse_args()
    source = validate_source(os.getenv("ANTHARES_LIVE_HLS_URL", DEFAULT_SOURCE))
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg_not_installed")
    source_preflight(source)
    print("ANTHARES_HLS_PREFLIGHT_OK=1", flush=True)
    if args.preflight:
        return 0
    if os.getenv("TIKTOK_LIVE_ACCOUNT_AUTHORIZED") != "true":
        raise RuntimeError("tiktok_account_authorization_required")
    if os.getenv("TIKTOK_LIVE_PRERECORDED_APPROVED") != "true":
        raise RuntimeError("prerecorded_programming_approval_required")
    if not 15 <= args.seconds <= MAX_SECONDS:
        raise RuntimeError("duration_out_of_range")
    destination = validate_destination(os.getenv("TIKTOK_LIVE_RTMP_DESTINATION", ""))
    command = build_command(source, destination, args.seconds)
    # The destination contains a secret: never log the command or stderr.
    with open(os.devnull, "wb") as sink:
        completed = subprocess.run(command, stdout=sink, stderr=sink,
                                   timeout=args.seconds + 90, check=False)
    if completed.returncode:
        raise RuntimeError("ffmpeg_ingest_failed_redacted")
    print("FFMPEG_PROCESS_COMPLETED=1", flush=True)
    # Completion alone is *not* proof that TikTok received or displayed the stream.
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        code = str(exc)
        if code.startswith("HTTP Error") or code.startswith("<urlopen error"):
            code = "hls_network_unavailable"
        print("ANTHARES_TIKTOK_STATUS=" + code[:100], file=sys.stderr)
        sys.exit(1)
