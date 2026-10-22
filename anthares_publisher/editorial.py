"""Universal, idempotent editorial metadata for Anthares public video posts.

Keeps a literal website in keyword/description fields: a dotted web address
is not a valid social hashtag. Never append the brand twice on retries.
"""
from __future__ import annotations

import re

_GENERIC_TAGS = {"#literatura", "#booktokbrasil", "#universoanthares", "#fyp", "#viral", "#paravoce", "#shorts"}
_GENERIC_HEADLINES = ("resumo da obra", "expectativa de live", "testando formato", "trecho da live", "assista agora")

from .unicode_gate import clean_publication_text, clean_metadata

SUFFIX = " ● Universo Anthares"
WEBSITE = "www.anthares.us"
_BRAND_END = re.compile(r"(?:\s*(?:●|•|\||[-–—])\s*Universo Anthares)+\s*$", re.I)
_WEBSITE = re.compile(r"(?<![\w.])(?:https?://)?(?:www\.)?anthares\.us(?:/)?(?![\w.])", re.I)


def branded_title(value: str, limit: int | None = None) -> str:
    """Format the human-readable title, leaving room for the exact suffix."""
    raw = " ".join(clean_publication_text(str(value or ""), field="title").split())
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
    existing = clean_publication_text(str(value or ""), field="text").strip() if value else ""
    if _WEBSITE.search(existing):
        return existing
    return (existing + " " if existing else "") + WEBSITE


STRATEGIC_POLICY = "anthares_editorial_transcript_v2"

def require_strategic_master(payload: dict) -> None:
    """Publication gate: a canonical clip must carry its own editorial metadata."""
    if not (payload.get("segment_id") or payload.get("cortes_clip_id")):
        return
    if payload.get("editorial_policy") != STRATEGIC_POLICY:
        raise ValueError("CORTES_STRATEGIC_METADATA_REQUIRED")
    title = str(payload.get("title") or payload.get("video_title") or "").strip()
    description = str(payload.get("description") or "").strip()
    keywords = payload.get("keywords")
    hashtags = payload.get("hashtags")
    if (not title.endswith(SUFFIX) or len(title) < 40 or
            title.casefold().startswith(("trecho ", "corte ", "live ", "vídeo "))):
        raise ValueError("CORTES_TITLE_NOT_CONTEXTUAL")
    core = title[:-len(SUFFIX)].strip().casefold()
    if any(term in core for term in _GENERIC_HEADLINES):
        raise ValueError("CORTES_TITLE_GENERIC_NOT_STRATEGIC")
    if len(description) < 70:
        raise ValueError("CORTES_DESCRIPTION_NOT_CONTEXTUAL")
    if (not isinstance(keywords, list) or len(keywords) < 3 or
            not all(isinstance(x, str) and len(x.strip()) >= 3 for x in keywords)):
        raise ValueError("CORTES_KEYWORDS_MISSING")
    if (not isinstance(hashtags, list) or not 2 <= len(hashtags) <= 5 or
            not all(isinstance(x, str) and re.fullmatch(r"#[^\W_]\w*", x, re.UNICODE) for x in hashtags)):
        raise ValueError("CORTES_HASHTAGS_MISSING")
    if len({x.casefold() for x in hashtags}) != len(hashtags):
        raise ValueError("CORTES_HASHTAGS_DUPLICATE")
    if not any(x.casefold() not in _GENERIC_TAGS for x in hashtags):
        raise ValueError("CORTES_HASHTAGS_NOT_CONTEXTUAL")


def prepare_publication_metadata(payload: dict, *, title_limit: int | None = None, include_inline_hashtags: bool = True) -> dict:
    """Decorate a destination payload without altering its identity or media URL.

    title is the editorial headline; text/description remain supplementary copy.
    For old text-only payloads the first nonempty line becomes the headline.
    """
    require_strategic_master(payload)
    data = clean_metadata(payload)
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
    relevant = [str(x).strip() for x in data.get("hashtags", [])
                if isinstance(x, str) and x.startswith("#")]
    unique = list(dict.fromkeys(relevant))
    for tag in unique:
        existing = re.sub(r"(?i)(?<!\w)"+re.escape(tag)+r"\b", "", existing).strip()
    body = data["title"] + ("\n" + existing if existing else "")
    if unique and include_inline_hashtags:
        body += "\n" + " ".join(unique)
    data["text"] = add_site_to_keywords(body)
    data["description"] = data["text"]
    if "keywords" in data:
        data["keywords"] = add_site_to_keywords(data["keywords"])
    if "tags" in data and isinstance(data["tags"], str):
        data["tags"] = add_site_to_keywords(data["tags"])
    return data
