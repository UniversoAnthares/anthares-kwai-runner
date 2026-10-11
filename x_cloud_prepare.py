#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CHANNEL_URL = os.getenv("X_SOURCE_CHANNEL", "https://www.youtube.com/@UniversoAnthares/streams")
SCAN_START = int(os.getenv("X_SCAN_START", "600"))
SCAN_SECONDS = int(os.getenv("X_SCAN_SECONDS", "300"))
WORK = Path(os.getenv("X_CLOUD_WORK", "x-cloud-work"))
MODEL = os.getenv("X_WHISPER_MODEL", "base")


def discover_source() -> dict:
    import yt_dlp
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": 12,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
    entries = list((info or {}).get("entries") or [])
    for e in entries:
        if not isinstance(e, dict):
            continue
        vid = str(e.get("id") or "").strip()
        if not vid:
            continue
        live = str(e.get("live_status") or "").lower()
        duration = int(e.get("duration") or 0)
        if live in {"is_live", "is_upcoming"}:
            continue
        if duration and duration < SCAN_START + 120:
            continue
        return {
            "video_id": vid,
            "source_url": f"https://www.youtube.com/watch?v={vid}",
            "title": str(e.get("title") or vid),
            "duration": duration,
        }
    raise RuntimeError("Nenhuma live concluída adequada encontrada no canal.")


def download_scan(source_url: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    end = SCAN_START + SCAN_SECONDS
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-warnings", "--no-progress",
        "--download-sections", f"*{SCAN_START}-{end}",
        "--force-keyframes-at-cuts",
        "--merge-output-format", "mp4",
        "-f", "bv*[height<=720]+ba/b[height<=720]/b",
        "-o", str(out),
        source_url,
    ]
    subprocess.run(cmd, check=True, timeout=900)
    if not out.exists() or out.stat().st_size < 100_000:
        raise RuntimeError("Trecho de varredura não foi baixado corretamente.")


def transcribe_words(video: Path) -> list[dict]:
    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(video), language="pt", beam_size=5,
        vad_filter=True, word_timestamps=True,
        condition_on_previous_text=True,
    )
    words = []
    idx = 0
    for seg in segments:
        for w in getattr(seg, "words", None) or []:
            text = str(getattr(w, "word", "") or "").strip()
            start = float(getattr(w, "start", 0.0) or 0.0)
            end = float(getattr(w, "end", start) or start)
            if not text or end <= start:
                continue
            words.append({"id": idx, "s": round(start, 3), "e": round(end, 3), "t": text})
            idx += 1
    if len(words) < 30:
        raise RuntimeError("Transcrição insuficiente para selecionar um corte.")
    return words


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    source = discover_source()
    scan = WORK / "scan.mp4"
    download_scan(source["source_url"], scan)
    words = transcribe_words(scan)
    payload = {
        "kind": "X_MICROCUT_REQUEST_V1",
        "account": "lucasyahn",
        "source": source,
        "scan_start": SCAN_START,
        "scan_seconds": SCAN_SECONDS,
        "target_seconds": {"min": 45, "max": 90},
        "instructions": {
            "select": "Escolha um trecho autossuficiente, forte e interessante, sem intro/CTA/bastidor.",
            "microcut": "Dentro dele remova repetição imediata, falso começo, correção substituída, fillers/hesitações prolongadas, espaços vazios e microapartes que não integram o fluxo. Preserve argumento, nuance e gramática.",
            "format": "Comente JSON X_MICROCUT_PLAN_V1 com start_word_id, end_word_id, remove [{from,to,reason}] e caption <=240 chars.",
        },
        "words": words,
    }
    Path("x-microcut-request.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print("X_MICROCUT_REQUEST_READY")
    print("X_SOURCE=" + source["source_url"])
    print("X_WORDS=" + str(len(words)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
