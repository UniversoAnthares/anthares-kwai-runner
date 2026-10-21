"""Mandatory Unicode pre-publication gate for every Anthares social channel.

Recover known accidental UTF-8 -> Windows OEM/ANSI mojibake. Fail closed when
recovery is ambiguous or malformed; no posting of malformed human-facing text.
"""
from __future__ import annotations
import re
import unicodedata

_BAD = re.compile(r"[\uFFFD├┬┤┐┘└┌┼╣╠╚╔│]|Ôù[Å]|Ã[^\s]|Â[^\s]|â[€œ€™€“]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SUFFIX = " ● Universo Anthares"


def _penalty(s: str) -> int:
    return len(_BAD.findall(s)) * 10 + s.count("\ufffd") * 100


def clean_publication_text(value: str, *, field: str = "text") -> str:
    if not isinstance(value, str):
        raise ValueError("publication_unicode_field_must_be_string:" + field)
    raw = unicodedata.normalize("NFC", value)
    candidates = [raw]
    if _penalty(raw):
        for encoding in ("cp850", "cp437", "cp1252", "latin-1"):
            try:
                recovered = raw.encode(encoding, errors="strict").decode("utf-8", errors="strict")
                candidates.append(unicodedata.normalize("NFC", recovered))
            except (UnicodeError, LookupError):
                pass
    result = min(candidates, key=_penalty)
    if _penalty(result) or _CONTROL.search(result):
        raise ValueError("publication_unicode_corrupt_blocked:" + field)
    if not result.strip():
        raise ValueError("publication_unicode_empty:" + field)
    return result


def clean_metadata(payload: dict) -> dict:
    output = dict(payload)
    for key in ("title", "video_title", "text", "description", "caption",
                "alt_text", "hashtags", "keywords", "tags"):
        if isinstance(output.get(key), str) and output[key].strip():
            output[key] = clean_publication_text(output[key], field=key)
    if isinstance(output.get("hashtags"), list):
        output["hashtags"] = [
            clean_publication_text(tag, field="hashtags") if isinstance(tag, str) else tag
            for tag in output["hashtags"]
        ]
    return output


def validate_final_publication(title: str, text: str) -> tuple[str, str]:
    """Last line of defence before any remote post/create/submit action."""
    headline = clean_publication_text(title, field="title")
    body = clean_publication_text(text, field="text")
    return headline, body
