#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

WHISPER_MODEL = os.getenv("ANTHARES_WHISPER_MODEL", "small").strip() or "small"
PAUSE_THRESHOLD = float(os.getenv("ANTHARES_PAUSE_SECONDS", "0.58") or 0.58)
PAUSE_KEEP = float(os.getenv("ANTHARES_PAUSE_KEEP_SECONDS", "0.14") or 0.14)
FILLER_MIN = float(os.getenv("ANTHARES_FILLER_MIN_SECONDS", "0.30") or 0.30)
MAX_REMOVAL_RATIO = float(os.getenv("ANTHARES_MAX_REMOVAL_RATIO", "0.32") or 0.32)
MIN_FINAL_SECONDS = float(os.getenv("ANTHARES_MIN_FINAL_SECONDS", "25") or 25)
MIN_REMOVED_SECONDS = float(os.getenv("ANTHARES_MIN_REMOVED_SECONDS", "0.18") or 0.18)
FUZZY_THRESHOLD = float(os.getenv("ANTHARES_RESTART_SIMILARITY", "0.82") or 0.82)

# Filler tokens are removed only when acoustically prolonged, duplicated, isolated by
# pauses, or part of a restart. This avoids deleting normal grammatical uses of "é".
FILLERS = {
    "ah", "ahn", "ha", "ham", "hum", "hmm", "eh", "e", "er", "uh", "uhm",
    "ne", "tipo", "assim",
}


def _exe(name: str) -> str:
    p = shutil.which(name)
    if not p:
        raise RuntimeError(f"{name} not found")
    return p


def duration(path: Path) -> float:
    p = subprocess.run([
        _exe("ffprobe"), "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], check=True, capture_output=True, text=True, timeout=60)
    return float(p.stdout.strip())


def norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def transcribe_words(path: Path) -> list[dict[str, Any]]:
    from faster_whisper import WhisperModel

    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(path), language="pt", beam_size=5, vad_filter=True,
        word_timestamps=True, condition_on_previous_text=True,
    )
    words: list[dict[str, Any]] = []
    for seg in segments:
        for item in getattr(seg, "words", None) or []:
            text = str(getattr(item, "word", "") or "").strip()
            start = float(getattr(item, "start", 0.0) or 0.0)
            end = float(getattr(item, "end", start) or start)
            probability = float(getattr(item, "probability", 1.0) or 0.0)
            if text and end > start:
                words.append({
                    "start": start, "end": end, "text": text,
                    "norm": norm(text), "probability": probability,
                })
    if not words:
        raise RuntimeError("Whisper produced no timestamped words")
    return words


def filler_pause_removals(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, w in enumerate(words):
        token = w["norm"]
        span = float(w["end"]) - float(w["start"])
        prev_token = words[i - 1]["norm"] if i else ""
        next_token = words[i + 1]["norm"] if i + 1 < len(words) else ""
        gap_before = float(w["start"]) - float(words[i - 1]["end"]) if i else 99.0
        gap_after = float(words[i + 1]["start"]) - float(w["end"]) if i + 1 < len(words) else 99.0
        isolated = gap_before >= 0.20 and gap_after >= 0.20
        duplicated = token and (token == prev_token or token == next_token)
        prolonged = span >= FILLER_MIN
        if token in FILLERS and (prolonged or duplicated or isolated):
            out.append({"start": w["start"], "end": w["end"], "reason": "filler"})

    for a, b in zip(words, words[1:]):
        gap = float(b["start"]) - float(a["end"])
        if gap >= PAUSE_THRESHOLD:
            half = PAUSE_KEEP / 2.0
            start = float(a["end"]) + half
            end = float(b["start"]) - half
            if end - start >= 0.10:
                out.append({"start": start, "end": end, "reason": "silence"})
    return out


def exact_repetition_removals(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = [w["norm"] for w in words]
    out: list[dict[str, Any]] = []
    occupied: set[int] = set()
    for size in range(8, 0, -1):
        i = 0
        while i + 2 * size <= len(tokens):
            left = tokens[i:i + size]
            right = tokens[i + size:i + 2 * size]
            if all(left) and left == right and not any(j in occupied for j in range(i, i + size)):
                if float(words[i + 2 * size - 1]["end"]) - float(words[i]["start"]) <= 10.0:
                    out.append({
                        "start": words[i]["start"],
                        "end": words[i + size - 1]["end"],
                        "reason": "immediate_repetition",
                    })
                    occupied.update(range(i, i + size))
                    i += 2 * size
                    continue
            i += 1
    return out


def fuzzy_restart_removals(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect false starts such as 'eu queria explicar... eu quero explicar'.

    Compares short phrase windows separated by at most three hesitation words. The
    earlier fragment plus hesitation is removed; the second, more complete attempt is kept.
    """
    tokens = [w["norm"] for w in words]
    out: list[dict[str, Any]] = []
    used_until = -1
    n = len(words)
    for i in range(n):
        if i <= used_until or not tokens[i]:
            continue
        best = None
        for size in range(7, 1, -1):
            if i + size >= n:
                continue
            left = tokens[i:i + size]
            if sum(bool(x) for x in left) < 2:
                continue
            for bridge in range(0, 4):
                j = i + size + bridge
                if j + size > n:
                    continue
                right = tokens[j:j + size]
                if sum(bool(x) for x in right) < 2:
                    continue
                ratio = difflib.SequenceMatcher(None, left, right).ratio()
                same_start = left[0] == right[0]
                span = float(words[j + size - 1]["end"]) - float(words[i]["start"])
                if ratio >= FUZZY_THRESHOLD and same_start and span <= 12.0:
                    score = (ratio, size, -bridge)
                    if best is None or score > best[0]:
                        best = (score, j)
        if best:
            j = best[1]
            # Preserve a tiny breath before the clean restart.
            end = max(float(words[i]["start"]), float(words[j]["start"]) - 0.06)
            if end - float(words[i]["start"]) >= 0.16:
                out.append({
                    "start": float(words[i]["start"]),
                    "end": end,
                    "reason": "fuzzy_restart",
                })
                used_until = j - 1
    return out


def stutter_removals(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        if a["norm"] and a["norm"] == b["norm"]:
            gap = float(b["start"]) - float(a["end"])
            if gap <= 0.45:
                out.append({"start": a["start"], "end": a["end"], "reason": "stutter"})
    return out


def merge_removals(rows: list[dict[str, Any]], total: float) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        a = max(0.0, float(row["start"]))
        b = min(total, float(row["end"]))
        if b - a >= 0.08:
            cleaned.append({"start": a, "end": b, "reasons": [str(row["reason"])]})
    cleaned.sort(key=lambda x: (x["start"], x["end"]))
    merged: list[dict[str, Any]] = []
    for row in cleaned:
        if not merged or row["start"] > merged[-1]["end"] + 0.06:
            merged.append(row)
        else:
            merged[-1]["end"] = max(merged[-1]["end"], row["end"])
            merged[-1]["reasons"].extend(row["reasons"])

    budget = min(total * min(max(MAX_REMOVAL_RATIO, 0.0), 0.45), max(0.0, total - MIN_FINAL_SECONDS))
    accepted: list[dict[str, Any]] = []
    used = 0.0
    # Preserve semantic repairs/repetitions ahead of cosmetic silence when budget is tight.
    priority = {"fuzzy_restart": 0, "immediate_repetition": 1, "stutter": 2, "filler": 3, "silence": 4}
    ranked = sorted(merged, key=lambda r: (min(priority.get(x, 9) for x in r["reasons"]), r["start"]))
    for row in ranked:
        span = row["end"] - row["start"]
        if used + span <= budget + 1e-6:
            accepted.append(row)
            used += span
    return sorted(accepted, key=lambda x: x["start"])


def render_without(path: Path, removals: list[dict[str, Any]], output: Path) -> None:
    total = duration(path)
    cursor = 0.0
    keep: list[tuple[float, float]] = []
    edge = 0.025
    for row in removals:
        a = max(cursor, float(row["start"]) - edge)
        b = min(total, float(row["end"]) + edge)
        if a > cursor + 0.025:
            keep.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < total - 0.025:
        keep.append((cursor, total))
    if not keep:
        raise RuntimeError("microcut would remove entire video")

    filters: list[str] = []
    concat: list[str] = []
    for idx, (a, b) in enumerate(keep):
        filters.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{idx}]")
        filters.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{idx}]")
        concat.append(f"[v{idx}][a{idx}]")
    filters.append("".join(concat) + f"concat=n={len(keep)}:v=1:a=1[vout][aout]")
    subprocess.run([
        _exe("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
        "-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output),
    ], check=True, timeout=1800)


def transcript(words: list[dict[str, Any]]) -> str:
    return " ".join(str(w["text"]) for w in words).strip()


def run(source: Path, output: Path) -> dict[str, Any]:
    original = duration(source)
    words = transcribe_words(source)
    candidates = []
    candidates += fuzzy_restart_removals(words)
    candidates += exact_repetition_removals(words)
    candidates += stutter_removals(words)
    candidates += filler_pause_removals(words)
    removals = merge_removals(candidates, original)
    if not removals:
        raise RuntimeError("no meaningful microcuts detected")
    render_without(source, removals, output)
    final = duration(output)
    removed = max(0.0, original - final)
    if final < MIN_FINAL_SECONDS:
        raise RuntimeError("microcut result below minimum duration")
    if removed < MIN_REMOVED_SECONDS:
        raise RuntimeError("microcut removed too little audio to prove editing")
    reasons: dict[str, int] = {}
    for row in removals:
        for reason in row["reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "engine": "anthares_microcut_v2",
        "whisper_model": WHISPER_MODEL,
        "original_duration": round(original, 3),
        "final_duration": round(final, 3),
        "removed_seconds": round(removed, 3),
        "removed_ratio": round(removed / original, 4) if original else 0.0,
        "word_count": len(words),
        "intervals": len(removals),
        "reasons": reasons,
        "removals": [
            {"start": round(r["start"], 3), "end": round(r["end"], 3), "reasons": sorted(set(r["reasons"]))}
            for r in removals
        ],
        "transcript": transcript(words),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("output")
    p.add_argument("--report", default="microcut-report.json")
    args = p.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    report = run(source, output)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
