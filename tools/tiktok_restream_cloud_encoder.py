#!/usr/bin/env python3
"""Read-only proof for a cloud FFmpeg encoder, using Anthares's public HLS VOD.

The preflight never reads a stream key, changes a LIVE room, or sends RTMP.
Everything is temporary on a GitHub-hosted standard Linux runner.
"""
import argparse
import os
import pathlib
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request

SOURCE = "https://anthares.us/wp-content/uploads/anthares-live-static/vod/index.m3u8"
MAX_SECONDS = 21600
LINE_RE = re.compile(r"^[A-Za-z0-9._-]+\.ts$")


def fetch_manifest():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "Anthares-Cloud-Preflight/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError("source_not_ok")
        raw = response.read(1024 * 1024).decode("utf-8")
    lines = raw.splitlines()
    if not lines or lines[0] != "#EXTM3U":
        raise RuntimeError("invalid_manifest")
    parts = []
    elapsed = 0.0
    discontinuities = 0
    for i, line in enumerate(lines):
        if line.strip() == "#EXT-X-DISCONTINUITY":
            discontinuities += 1
        elif line.startswith("#EXTINF:"):
            length = float(line.split(":", 1)[1].split(",", 1)[0])
            uri = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if not LINE_RE.fullmatch(uri):
                raise RuntimeError("invalid_segment_name")
            parts.append((elapsed, length, urllib.parse.urljoin(SOURCE, uri), discontinuities))
            elapsed += length
            discontinuities = 0
    if elapsed < MAX_SECONDS + 10 or len(parts) < 100:
        raise RuntimeError("incomplete_six_hour_program")
    print("CLOUD_SOURCE=PASS segments={} duration_seconds={:.0f}".format(len(parts), elapsed), flush=True)
    return parts


def write_playlist(parts, position, path):
    idx = next((i for i, row in enumerate(parts) if row[0] + row[1] > position), None)
    if idx is None:
        raise RuntimeError("resume_position_out_of_range")
    previous = sum(row[3] for row in parts[:idx])
    output = [
        "#EXTM3U", "#EXT-X-VERSION:6", "#EXT-X-TARGETDURATION:12",
        "#EXT-X-MEDIA-SEQUENCE:" + str(idx),
        "#EXT-X-DISCONTINUITY-SEQUENCE:" + str(previous),
        "#EXT-X-PLAYLIST-TYPE:VOD", "#EXT-X-INDEPENDENT-SEGMENTS"
    ]
    for _, length, uri, has_discontinuity in parts[idx:]:
        if has_discontinuity:
            output.append("#EXT-X-DISCONTINUITY")
        output.append("#EXTINF:{:.6f},".format(length))
        output.append(uri)
    output.append("#EXT-X-ENDLIST")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")
    path.chmod(0o600)
    residual = max(0.0, position - parts[idx][0])
    return residual


def make_args(playlist, residual, seconds, destination):
    return [
        "ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-re", "-ss", "{:.6f}".format(residual),
        "-protocol_whitelist", "file,crypto,data,http,https,tcp,tls", "-i", str(playlist),
        "-t", str(seconds), "-c:v", "copy", "-c:a", "aac",
        "-af", "aresample=async=1:first_pts=0,asetpts=N/SR/TB",
        "-b:a", "128k", "-ar", "44100", "-avoid_negative_ts", "make_zero",
        "-f", "flv", "-progress", "pipe:1", destination
    ]


def preflight(offsets):
    parts = fetch_manifest()
    with tempfile.TemporaryDirectory(prefix="anthares-restream-cloud-") as root:
        for offset in offsets:
            playlist = pathlib.Path(root) / "source.m3u8"
            residual = write_playlist(parts, offset, playlist)
            # Output is local, ephemeral and contains no RTMP key.
            cmd = make_args(playlist, residual, 8, os.devnull)
            completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       timeout=60, text=True)
            if completed.returncode or "progress=end" not in completed.stdout or "out_time=" not in completed.stdout:
                detail = completed.stderr[-900:].replace(SOURCE, "[PUBLIC_SOURCE]")
                print("CLOUD_RESUME_TEST=FAILED offset={} rc={} detail={}".format(offset, completed.returncode, repr(detail)), flush=True)
                raise RuntimeError("cloud_encoder_preflight_failed")
            print("CLOUD_RESUME_TEST=PASS offset={} progress=end".format(offset), flush=True)
    print("CLOUD_PREFLIGHT_COMPLETE=1", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preflight", action="store_true")
    args = p.parse_args()
    if not args.preflight:
        raise SystemExit("read_only_cloud_preflight_only")
    preflight([3600, 10400, 20000])


if __name__ == "__main__":
    main()
