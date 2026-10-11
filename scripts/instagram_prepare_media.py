#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from instagram_autopublish import clean_caption, fetch_media, load_ledger, select_next

WORK_DIR = Path(os.getenv("INSTAGRAM_PREPARE_DIR", "instagram-prepared"))
PLAN_PATH = Path(os.getenv("INSTAGRAM_PREPARED_PLAN", "instagram-prepared.json"))
WHISPER_MODEL = os.getenv("INSTAGRAM_WHISPER_MODEL", "small").strip() or "small"
PAUSE_THRESHOLD = float(os.getenv("INSTAGRAM_PAUSE_SECONDS", "0.65") or 0.65)
PAUSE_KEEP = float(os.getenv("INSTAGRAM_PAUSE_KEEP_SECONDS", "0.16") or 0.16)
FILLER_MIN = float(os.getenv("INSTAGRAM_FILLER_MIN_SECONDS", "0.45") or 0.45)
MAX_REMOVAL_RATIO = float(os.getenv("INSTAGRAM_MAX_REMOVAL_RATIO", "0.30") or 0.30)
MIN_FINAL_SECONDS = float(os.getenv("INSTAGRAM_MIN_FINAL_SECONDS", "30") or 30)
FILLERS = {"ah", "ahn", "ha", "ham", "hum", "hmm", "eh", "e", "er", "uh", "uhm", "ne", "tipo"}
MIN_MICROCUT_SECONDS = float(os.getenv("INSTAGRAM_MIN_MICROCUT_SECONDS", "0.20"))


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found")
    return exe


def ffprobe() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe not found")
    return exe


def duration(path: Path) -> float:
    proc = subprocess.run(
        [ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True, timeout=60,
    )
    return float(proc.stdout.strip())


def dimensions(path: Path) -> tuple[int, int]:
    proc = subprocess.run(
        [ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(path)],
        check=True, capture_output=True, text=True, timeout=60,
    )
    w, h = proc.stdout.strip().split("x", 1)
    return int(w), int(h)


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://anthares.us/"})
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    if path.stat().st_size < 250_000:
        raise RuntimeError("downloaded source video is unexpectedly small")


def _norm(text: str) -> str:
    import unicodedata
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
    for idx, seg in enumerate(segments):
        del idx
        for word in getattr(seg, "words", None) or []:
            text = str(getattr(word, "word", "") or "").strip()
            start = float(getattr(word, "start", 0.0) or 0.0)
            end = float(getattr(word, "end", start) or start)
            if text and end > start:
                words.append({"start": start, "end": end, "text": text, "norm": _norm(text)})
    if not words:
        raise RuntimeError("Whisper produced no timestamped words")
    return words


def filler_and_pause_removals(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, word in enumerate(words):
        token = word["norm"]
        span = float(word["end"]) - float(word["start"])
        prev_token = words[i - 1]["norm"] if i else ""
        next_token = words[i + 1]["norm"] if i + 1 < len(words) else ""
        if token in FILLERS and (span >= FILLER_MIN or token == prev_token or token == next_token):
            out.append({"start": float(word["start"]), "end": float(word["end"]), "reason": "filler"})

    for a, b in zip(words, words[1:]):
        gap = float(b["start"]) - float(a["end"])
        if gap >= PAUSE_THRESHOLD:
            half = PAUSE_KEEP / 2.0
            start = float(a["end"]) + half
            end = float(b["start"]) - half
            if end - start >= 0.12:
                out.append({"start": start, "end": end, "reason": "silence"})
    return out


def repeated_phrase_removals(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = [w["norm"] for w in words]
    out: list[dict[str, Any]] = []
    occupied: set[int] = set()
    # Longest exact immediate repetitions first: "eu acho que / eu acho que".
    for size in range(8, 0, -1):
        i = 0
        while i + 2 * size <= len(tokens):
            first = tokens[i:i + size]
            second = tokens[i + size:i + 2 * size]
            if (
                all(first)
                and first == second
                and not any(j in occupied for j in range(i, i + size))
                and float(words[i + size - 1]["end"]) - float(words[i]["start"]) <= 8.0
            ):
                out.append({
                    "start": float(words[i]["start"]),
                    "end": float(words[i + size - 1]["end"]),
                    "reason": "immediate_repetition",
                })
                occupied.update(range(i, i + size))
                i += 2 * size
            else:
                i += 1
    # Repeated discourse restart with a short hesitation between the two phrases.
    for size in range(6, 1, -1):
        for i in range(len(tokens) - 2 * size + 1):
            left = tokens[i:i + size]
            right = tokens[i + size:i + 2 * size]
            if all(left) and left == right and words[i + size]["start"] - words[i + size - 1]["end"] <= 1.2:
                out.append({"start": float(words[i]["start"]), "end": float(words[i + size - 1]["end"]), "reason": "restart"})
    return out


def merge_removals(rows: list[dict[str, Any]], total: float) -> list[dict[str, Any]]:
    cleaned = []
    for row in rows:
        a = max(0.0, float(row["start"]))
        b = min(total, float(row["end"]))
        if b - a >= 0.10:
            cleaned.append({"start": a, "end": b, "reasons": [str(row["reason"])]})
    cleaned.sort(key=lambda x: (x["start"], x["end"]))
    merged: list[dict[str, Any]] = []
    for row in cleaned:
        if not merged or row["start"] > merged[-1]["end"] + 0.08:
            merged.append(row)
        else:
            merged[-1]["end"] = max(merged[-1]["end"], row["end"])
            merged[-1]["reasons"].extend(row["reasons"])

    budget = min(total * min(max(MAX_REMOVAL_RATIO, 0.0), 0.45), max(0.0, total - MIN_FINAL_SECONDS))
    accepted = []
    used = 0.0
    for row in sorted(merged, key=lambda x: (x["end"] - x["start"], x["start"])):
        span = row["end"] - row["start"]
        if used + span <= budget + 1e-6:
            accepted.append(row)
            used += span
    return sorted(accepted, key=lambda x: x["start"])


def render_without(path: Path, removals: list[dict[str, Any]], output: Path) -> None:
    total = duration(path)
    cursor = 0.0
    keep: list[tuple[float, float]] = []
    edge = 0.035
    for row in removals:
        a = max(cursor, float(row["start"]) - edge)
        b = min(total, float(row["end"]) + edge)
        if a > cursor + 0.03:
            keep.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < total - 0.03:
        keep.append((cursor, total))
    if not keep:
        raise RuntimeError("microcut would remove the entire video")

    filters = []
    concat = []
    for idx, (a, b) in enumerate(keep):
        filters.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{idx}]")
        filters.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{idx}]")
        concat.append(f"[v{idx}][a{idx}]")
    filters.append("".join(concat) + f"concat=n={len(keep)}:v=1:a=1[vout][aout]")
    subprocess.run(
        [ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", str(output)],
        check=True, timeout=1200,
    )


def microcut(path: Path, output: Path) -> dict[str, Any]:
    original = duration(path)
    words = transcribe_words(path)
    candidates = filler_and_pause_removals(words) + repeated_phrase_removals(words)
    removals = merge_removals(candidates, original)
    if removals:
        render_without(path, removals, output)
    else:
        shutil.copy2(path, output)
    final = duration(output)
    if final < MIN_FINAL_SECONDS:
        raise RuntimeError("microcut duration below minimum; source must be reselected")
    if original - final < MIN_MICROCUT_SECONDS:
        raise RuntimeError("no meaningful microcuts detected; refusing unedited clip")
    reasons: dict[str, int] = {}
    for row in removals:
        for reason in row.get("reasons", []):
            reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "original_duration": round(original, 3),
        "final_duration": round(final, 3),
        "removed_seconds": round(max(0.0, original - final), 3),
        "removed_ratio": round(max(0.0, original - final) / original, 4) if original else 0.0,
        "word_count": len(words),
        "intervals": len(removals),
        "reasons": reasons,
    }


def verticalize(path: Path, output: Path) -> dict[str, Any]:
    before = duration(path)
    w, h = dimensions(path)
    # Preserve existing 9:16 media exactly; future TikTok microcuts arrive here already vertical.
    if h > 0 and abs((w / h) - (9 / 16)) < 0.001:
        shutil.copy2(path, output)
        return {"source_dimensions": [w, h], "output_dimensions": [w, h], "reencoded": False}
    subprocess.run(
        [ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", str(output)],
        check=True, timeout=1200,
    )
    after = duration(output)
    if abs(after - before) > 1.5:
        raise RuntimeError(f"vertical render changed duration too much: {before:.2f} -> {after:.2f}")
    ow, oh = dimensions(output)
    return {"source_dimensions": [w, h], "output_dimensions": [ow, oh], "reencoded": True}


def prepare() -> dict[str, Any]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ledger = load_ledger()
    rows = fetch_media()
    probe_ledger = json.loads(json.dumps(ledger))
    row = None
    source_url = ""
    source = WORK_DIR / "source.mp4"
    while True:
        candidate = select_next(rows, probe_ledger, allow_legacy=True)
        if candidate is None:
            break
        candidate_url = str(candidate.get("source_url") or "")
        try:
            download(candidate_url, source)
            row = candidate
            source_url = candidate_url
            break
        except Exception as exc:
            key = str(candidate.get("id") or candidate_url)
            probe_ledger.setdefault("published", {})[key] = {"source_url": candidate_url}
            print(f"INSTAGRAM_SOURCE_SKIP id={candidate.get('id')} error={type(exc).__name__}: {exc}", flush=True)
            source.unlink(missing_ok=True)
    if row is None:
        plan = {"ready": False, "reason": "no_reachable_unpublished_owned_media"}
        PLAN_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return plan
    source_is_microcut = "-microcut" in source_url.casefold()
    micro = WORK_DIR / "microcut.mp4"
    # A filename alone cannot prove that TikTok microcuts were applied.
    micro_meta = microcut(source, micro)
    micro_meta["reused_existing_tiktok_microcut"] = False
    micro_meta["source_marked_microcut"] = source_is_microcut

    final = WORK_DIR / f"instagram-{row.get('id') or 'clip'}-microcut.mp4"
    layout_meta = verticalize(micro, final)
    plan = {
        "ready": True,
        "source_attachment_id": str(row.get("id") or ""),
        "source_url": source_url,
        "caption": clean_caption(row),
        "media_path": str(final),
        "asset_name": final.name,
        "microcut": micro_meta,
        "layout": layout_meta,
        "final_duration": round(duration(final), 3),
    }
    PLAN_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return plan


def main() -> int:
    result = prepare()
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
