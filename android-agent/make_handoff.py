#!/usr/bin/env python3
"""Create a physical-Android Anthares -> official Kwai video handoff link.

The input file must be byte-identical to the HTTPS media served by anthares.us.
The link contains no authentication material, cookies or passwords.
"""
import argparse
import hashlib
from pathlib import Path
from urllib.parse import urlencode, urlsplit


def make_link(video: Path, public_url: str) -> str:
    parsed = urlsplit(public_url)
    if (parsed.scheme != "https" or parsed.hostname not in
            {"anthares.us", "www.anthares.us"} or parsed.username or
            parsed.password or parsed.port is not None):
        raise ValueError("Only public HTTPS anthares.us media URLs are allowed")
    if video.stat().st_size > 250 * 1024 * 1024 or video.stat().st_size == 0:
        raise ValueError("Video must be nonempty and <=250 MiB")
    digest = hashlib.sha256()
    with video.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return "anthares-kwai://send?" + urlencode({
        "url": public_url, "sha256": digest.hexdigest()
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    print(make_link(args.video, args.url))


if __name__ == "__main__":
    main()
