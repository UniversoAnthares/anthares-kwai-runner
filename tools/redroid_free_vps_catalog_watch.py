#!/usr/bin/env python3
"""Read-only catalog check for zero-cost, persistent ReDroid VPS candidates.

Never registers accounts, requests a VPS, sends credentials or triggers payments.
Page listings do NOT prove root access, actual allocation, kernel binder,
provider legitimacy or permission to run social-media apps.
"""
import html
from html.parser import HTMLParser
import json
from datetime import datetime, timezone
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CATALOG = {
    "vpsfree": "https://vpsfree.io/plans",
    "verta": "https://portal.vertacloud.biz/index.php?rp=/store/free-vps",
    "nanokvm": "https://nanokvm.net/index.php?p=deploy",
    "nevatal": "https://cloud.nevatal.id/",
}
MAX_BYTES = 300_000
TIMEOUT_SECONDS = 16


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.words = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.words.append(data.strip())


def normalized_markup(markup):
    collector = PageText()
    collector.feed(markup)
    return re.sub(r"\s+", " ", html.unescape(" ".join(collector.words))).strip()


def evaluate(name, status_code, text):
    """Classify evidence conservatively; no catalog status ever approves access."""
    low = text.casefold()
    if status_code != 200:
        return "ORIGIN_UNAVAILABLE" if status_code in (408, 429, 500, 502, 503, 530) else "HTTP_ERROR"
    if name == "vpsfree":
        # Marketed tiers above the plan table do not establish a free offer.
        if "192mb nat vps" in low and ("$0.00" in low or "free" in low):
            return "FREE_LISTING_BELOW_REDRIOD_MINIMUM"
        return "FREE_CATALOG_UNVERIFIED"
    if name == "verta":
        if "4gb ram" in low and ("free" in low or "grátis" in low):
            return "FOUR_GB_ADVERTISED_NO_DELIVERY_PROOF"
        return "FREE_CATALOG_UNVERIFIED"
    if name == "nanokvm":
        if "1 core" in low and "2048mb" in low:
            return "ONE_CORE_TWO_GB_NOT_QUALIFIED"
        return "COMMUNITY_ELIGIBILITY_AND_RESOURCES_UNVERIFIED"
    if name == "nevatal":
        if "android" in low and ("free" in low or "grátis" in low):
            return "ANDROID_OFFER_UNVERIFIED_NO_HOST"
        return "SERVICE_UNVERIFIED"
    return "UNKNOWN_PROVIDER"


def fetch_public(name, url):
    # URL is compile-time fixed; no user-controlled target, path or token.
    req = Request(url, headers={"User-Agent": "Anthares-ReDroid-Free-VPS-Catalog/1.0"})
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            if response.geturl().split("/")[2].lower() != url.split("/")[2].lower():
                return {"provider": name, "status": "CROSS_HOST_REDIRECT_REFUSED"}
            status = response.status
            payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            return {"provider": name, "status": "PAGE_TOO_LARGE"}
        page = normalized_markup(payload.decode("utf-8", errors="replace"))
        return {"provider": name, "status": evaluate(name, status, page),
                "http_status": status}
    except HTTPError as exc:
        return {"provider": name, "status": evaluate(name, exc.code, ""),
                "http_status": exc.code}
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError):
        return {"provider": name, "status": "FETCH_UNAVAILABLE"}


def report():
    results = [fetch_public(k, url) for k, url in CATALOG.items()]
    return {
        "schema": "anthares.redroid.free_vps_catalog.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "any_vm_allocated": False,
        "any_provider_approved": False,
        "secrets_used": False,
        "next_gate": "ACCOUNT_ELIGIBILITY_AND_REAL_VM_DELIVERY_PROOF",
    }


def main():
    print(json.dumps(report(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
