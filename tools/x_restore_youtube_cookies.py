#!/usr/bin/env python3
"""Restore YouTube cookie file on a short-lived GitHub-hosted runner only."""
import base64
import os
from pathlib import Path

def main():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise RuntimeError("X_COOKIE_RESTORE_GITHUB_ONLY")
    b64 = os.getenv("YOUTUBE_COOKIES_B64", "").strip()
    if not b64:
        print("X_YOUTUBE_COOKIE_FALLBACK_UNCONFIGURED")
        return
    try:
        value = base64.b64decode(b64, validate=True)
        if not (120 <= len(value) <= 2_000_000 and b"youtube.com" in value.lower()):
            raise ValueError("invalid cookies")
        target = Path(os.environ["RUNNER_TEMP"]) / "anthares-x-ytcookies.txt"
        target.write_bytes(value)
        target.chmod(0o600)
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
            stream.write("X_YT_COOKIE_FILE=" + str(target) + "\n")
        print("X_YOUTUBE_COOKIE_ROUTE_READY")
    except Exception:
        print("X_YOUTUBE_COOKIE_ROUTE_INVALID_PUBLIC_FALLBACK_ACTIVE")

if __name__ == "__main__":
    main()
