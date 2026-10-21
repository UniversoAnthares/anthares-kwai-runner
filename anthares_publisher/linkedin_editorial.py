"""LinkedIn-specific, contextual keywords without hashtag stuffing.

This applies to company and, once authorized separately, personal LinkedIn
destinations. No fixed unrelated trending tags, no invented claims. The same
master stays immutable and metadata is idempotent.
"""
from __future__ import annotations
import re
import unicodedata
from .editorial import branded_title, WEBSITE
from .unicode_gate import clean_publication_text

THEMES = (
    (("literatur", "livro", "livros", "autor", "escritor", "kafka", "romance",
      "narrativa", "leitura", "machado", "dostoievsk"), "#Literatura"),
    (("filosof", "aristotel", "platao", "socrates", "nietzsche", "etica",
      "conhecimento", "pensamento"), "#Filosofia"),
    (("mitolog", "lenda", "folclor", "deuses", "japonesa", "sobrenatural"), "#Mitologia"),
    (("histori", "seculo", "antiguidade", "medieval", "civilizac"), "#Historia"),
    (("poesi", "poeta", "verso", "poema", "soneto"), "#Poesia"),
    (("cultur", "arte", "teatro", "cinema", "criativ", "ficcao"), "#Cultura"),
    (("educa", "aprender", "estudo", "escola", "ensino"), "#Educacao"),
)
BASE = "#UniversoAnthares"


def _fold(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


def strategic_tags(title: str, description: str = "") -> tuple[str, ...]:
    clean_title = re.sub(r"(?:\s*[●•|–—-]\s*Universo Anthares)+\s*$", "", title, flags=re.I)
    text = _fold(clean_title + " " + description)
    found = [tag for needles, tag in THEMES if any(n in text for n in needles)]
    # Avoid duplicate editorial or source-provided tags.
    return (BASE, *found[:3]) if found else (BASE, "#LiteraturaECultura")


def linkedin_caption(title: str, description: str = "") -> str:
    headline = branded_title(title)
    raw = clean_publication_text(str(description or ""), field="text").strip()
    raw = re.sub(r"(?i)(?:https?://)?(?:www\.)?anthares\.us/?", "", raw).strip()
    raw = re.sub(r"(?i)#UniversoAnthares\b", "", raw).strip()
    tags = strategic_tags(title, raw)
    # Remove hashtags we will reinsert once in a stable order.
    for tag in tags:
        raw = re.sub(r"(?i)(?<!\w)" + re.escape(tag) + r"\b", "", raw)
    raw = " ".join(raw.split())
    tagline = "\n\n".join(filter(None, (headline, raw, WEBSITE, " ".join(tags))))
    if len(tagline) > 2200:
        max_desc = max(0, 2200 - len(headline) - len(WEBSITE) -
                       len(" ".join(tags)) - 8)
        raw = raw[:max_desc].rstrip(" .,;:\n")
        tagline = "\n\n".join(filter(None, (headline, raw, WEBSITE, " ".join(tags))))
    return tagline
