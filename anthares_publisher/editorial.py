"""Universal, idempotent editorial metadata for Anthares public video posts.

Keeps a literal website in keyword/description fields: a dotted web address
is not a valid social hashtag. Never append the brand twice on retries.
"""
from __future__ import annotations

import re

SUFFIX = " ● Universo Anthares"
WEBSITE = "www.anthares.us"
_BRAND_END = re.compile(r"(?:\s*(?:●|•|\||[-–—])\s*Universo Anthares)+\s*$", re.I)
_WEBSITE = re.compile(r"(?<![\w.])(?:https?://)?(?:www\.)?anthares\.us(?:/)?(?![\w.])", re.I)


def branded_title(value: str, limit: int | None = None) -> str:
    """Format the human-readable title, leaving room for the exact suffix."""
    raw = " ".join(str(value or "").split())
    raw = _BRAND_END.sub("", raw).strip(" \t-–—|●•")
    if not raw:
        raise ValueError("publication_title_required")
    if limit is not None:
        if limit <= len(SUFFIX):
            raise ValueError("publication_title_limit_below_brand_suffix")
        if len(raw) + len(SUFFIX) > limit:
            raw = raw[: limit - len(SUFFIX)].rstrip(" .,;:-–—|")
            if not raw:
                raise ValueError("publication_title_empty_after_truncation")
    return raw + SUFFIX


def add_site_to_keywords(value: str) -> str:
    """Use the literal URL as a keyword; dots must not be treated as hashtag syntax."""
    existing = str(value or "").strip()
    if _WEBSITE.search(existing):
        return existing
    return (existing + " " if existing else "") + WEBSITE


def prepare_publication_metadata(payload: dict, *, title_limit: int | None = None) -> dict:
    """Decorate a destination payload without altering its identity or media URL.

    title is the editorial headline; text/description remain supplementary copy.
    For old text-only payloads the first nonempty line becomes the headline.
    """
    data = dict(payload)
    headline = str(data.get("title") or "").strip()
    text = str(data.get("text") or data.get("description") or "").strip()
    if not headline:
        if not text:
            raise ValueError("publication_title_required")
        headline, _, continuation = text.partition("\n")
        text = continuation.strip()
    data["title"] = branded_title(headline, limit=title_limit)
    # Every supported textual description/keyword area receives the website.
    existing = text
    if existing.startswith(headline):
        existing = existing[len(headline):].strip()
    data["text"] = add_site_to_keywords(data["title"] + ("\n" + existing if existing else ""))
    data["description"] = data["text"]
    if "keywords" in data:
        data["keywords"] = add_site_to_keywords(data["keywords"])
    if "tags" in data and isinstance(data["tags"], str):
        data["tags"] = add_site_to_keywords(data["tags"])
    return data
