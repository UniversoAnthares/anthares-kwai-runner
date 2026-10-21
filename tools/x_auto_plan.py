#!/usr/bin/env python3
"""Autonomous editorial window selection for Anthares X long-form clips.

Uses timestamped Portuguese transcript already prepared by the CORTES source
job; avoids a mandatory external AI/manual comment dependency.
"""
from __future__ import annotations

import bisect
import json
import re
import unicodedata
from pathlib import Path

STOP = {"para", "com", "que", "uma", "dos", "das", "esta", "isso", "esse", "essa",
        "voce", "eles", "elas", "nosso", "entre", "sobre", "porque"}
CTA = {"inscreva", "inscrever", "like", "curta", "compartilhe", "superchat", "membro"}


def word(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    return re.sub(r"[^a-z0-9]+", "", text.encode("ascii", "ignore").decode().lower())


def choose(words, min_duration=520.0, max_duration=760.0):
    if len(words) < 200:
        raise ValueError("X_AUTO_PLAN_TRANSCRIPT_TOO_SHORT")
    ends = [float(w["e"]) for w in words]
    candidates = []
    for i in range(0, len(words), 12):
        start = float(words[i]["s"])
        j = bisect.bisect_left(ends, start + 635.0, lo=i + 1)
        for k in range(max(i + 1, j - 28), min(len(words), j + 29), 7):
            span = ends[k] - start
            if not min_duration <= span <= max_duration:
                continue
            segment = words[i:k + 1]
            lexical = [word(x["t"]) for x in segment]
            useful = [t for t in lexical if len(t) > 3 and t not in STOP]
            diversity = len(set(useful))
            density = len(segment) / span
            cta = sum(t in CTA for t in lexical)
            punctuation = sum(str(x["t"]).endswith((".", "?", "!")) for x in segment)
            boundary = (
                12 if i == 0 or str(words[i - 1]["t"]).endswith((".", "!", "?")) else 0
            ) + (18 if str(words[k]["t"]).endswith((".", "!", "?")) else 0)
            score = diversity * .6 + density * 75 + punctuation * .7 + boundary
            score -= cta * 15 + abs(span - 635) * .05
            candidates.append((score, i, k))
    if not candidates:
        raise ValueError("X_AUTO_PLAN_NO_LONG_COMPLETE_SEGMENT")
    _, lo, hi = max(candidates)
    return lo, hi


def plan(request):
    if (request.get("kind") != "X_MICROCUT_REQUEST_V1"
            or request.get("account") != "lucasyahn"):
        raise ValueError("X_AUTO_PLAN_WRONG_CONTRACT")
    policy = request.get("output_policy") or {}
    if (policy.get("orientation"), policy.get("aspect_ratio"),
            policy.get("source_class")) != ("horizontal", "16:9", "long_form"):
        raise ValueError("X_AUTO_PLAN_WRONG_MEDIA_POLICY")
    words = request.get("words") or []
    lo, hi = choose(words)
    title = str((request.get("source") or {}).get("title") or "").strip()
    intro = " ".join(str(w["t"]) for w in words[lo:lo + 23])
    intro = re.sub(r"\s+([.,!?;:])", r"\1", intro)
    title = title[:80].strip()
    caption = (title + ": " if title else "") + intro
    caption = caption[:220].rsplit(" ", 1)[0].rstrip(".,;: ")
    if not caption:
        raise ValueError("X_AUTO_PLAN_CAPTION_EMPTY")
    return {"kind": "X_MICROCUT_PLAN_V1",
            "start_word_id": int(words[lo]["id"]),
            "end_word_id": int(words[hi]["id"]),
            "remove": [],
            "caption": caption[:240]}


def main():
    request = json.loads(Path("x-microcut-request.json").read_text(encoding="utf-8"))
    obj = plan(request)
    Path("x-microcut-plan.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("X_AUTO_LONG_PLAN_VALIDATED start=" + str(obj["start_word_id"]) +
          " end=" + str(obj["end_word_id"]))


if __name__ == "__main__":
    main()
