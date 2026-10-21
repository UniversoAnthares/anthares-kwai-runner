#!/usr/bin/env python3
"""Read-only Buffer LinkedIn account discovery: never log account IDs or names."""
from __future__ import annotations
import json
import urllib.parse

from social_adapters.buffer_three_channels import channels, PINNED_CHANNELS

COMPANY_ID = PINNED_CHANNELS["linkedin"][0]


def classify(items):
    company = False
    personal = 0
    ambiguous = 0
    for item in items:
        if str(item.get("service") or "").lower() != "linkedin":
            continue
        link = str(item.get("externalLink") or "").strip()
        if link and "://" not in link:
            link = "https://" + link.lstrip("/")
        parsed = urllib.parse.urlparse(link)
        host = (parsed.hostname or "").lower().removeprefix("www.")
        path = parsed.path.rstrip("/").lower()
        if str(item.get("id") or "") == COMPANY_ID and host == "linkedin.com" and path == "/company/145345334":
            company = True
        elif host == "linkedin.com" and path.startswith("/in/"):
            personal += 1
        else:
            ambiguous += 1
    return {"company_verified": company,
            "personal_profiles_connected": personal,
            "ambiguous_linkedin_channels": ambiguous}


def main():
    # Read-only GraphQL organizations/channels; no publish or token echo.
    try:
        result = classify(channels())
    except Exception:
        result = {"company_verified": None,
                  "personal_profiles_connected": None,
                  "ambiguous_linkedin_channels": None,
                  "read_error": "buffer_channel_listing_unavailable"}
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["company_verified"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
