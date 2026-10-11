#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

CHANNEL_URL = os.getenv("X_SOURCE_CHANNEL", "https://www.youtube.com/@UniversoAnthares/streams")
SCAN_START = int(os.getenv("X_SCAN_START", "600"))
SCAN_SECONDS = int(os.getenv("X_SCAN_SECONDS", "300"))
WORK = Path(os.getenv("X_CLOUD_WORK", "x-cloud-work"))
MODEL = os.getenv("X_WHISPER_MODEL", "base")
INVIDIOUS_BASES = tuple(
    x.strip().rstrip("/") for x in os.getenv(
        "X_INVIDIOUS_BASES",
        "https://invidious.f5.si,https://iv.ggtyler.dev,https://inv.nadeko.net,https://yewtu.be",
    ).split(",") if x.strip()
)


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


def _video_id(source_url: str) -> str:
    p = urllib.parse.urlparse(source_url)
    if p.hostname in {"youtu.be", "www.youtu.be"}:
        value = p.path.strip("/")
    else:
        value = urllib.parse.parse_qs(p.query).get("v", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value or ""):
        raise RuntimeError("URL de origem do YouTube sem video id válido.")
    return value


def _format_height(row: dict) -> int:
    try:
        return int(row.get("height") or 0)
    except Exception:
        return 0


def _fetch_invidious_streams(video_id: str) -> tuple[str, str, str]:
    errors = []
    for base in INVIDIOUS_BASES:
        for local in ("true", "false"):
            try:
                url = f"{base}/api/v1/videos/{video_id}?local={local}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = json.load(r)
                adaptive = [x for x in (data.get("adaptiveFormats") or []) if isinstance(x, dict) and x.get("url")]
                videos = [x for x in adaptive if str(x.get("type") or x.get("mimeType") or "").startswith("video/")]
                audios = [x for x in adaptive if str(x.get("type") or x.get("mimeType") or "").startswith("audio/")]
                # Some instances expose codec/type strings differently. Fall back to dimensions/bitrate.
                if not videos:
                    videos = [x for x in adaptive if _format_height(x) > 0 and str(x.get("audioQuality") or "") == ""]
                if not audios:
                    audios = [x for x in adaptive if _format_height(x) == 0 and int(x.get("bitrate") or 0) > 0]
                if not videos or not audios:
                    errors.append(f"{base} local={local}: no split streams")
                    continue
                eligible = [x for x in videos if 0 < _format_height(x) <= 720]
                if not eligible:
                    eligible = videos
                video = max(eligible, key=lambda x: (_format_height(x), int(x.get("bitrate") or 0)))
                audio = max(audios, key=lambda x: int(x.get("bitrate") or 0))
                print(
                    f"X_SOURCE_FALLBACK=INVIDIOUS base={base} local={local} "
                    f"height={_format_height(video)} audio_bitrate={int(audio.get('bitrate') or 0)}",
                    flush=True,
                )
                return str(video["url"]), str(audio["url"]), f"{base}|local={local}"
            except Exception as exc:
                errors.append(f"{base} local={local}: {type(exc).__name__}: {str(exc)[:120]}")
    raise RuntimeError("Invidious sem stream utilizável: " + " | ".join(errors[-8:]))


def _download_scan_invidious(source_url: str, out: Path) -> None:
    video_id = _video_id(source_url)
    video_url, audio_url, route = _fetch_invidious_streams(video_id)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(SCAN_START), "-i", video_url,
        "-ss", str(SCAN_START), "-i", audio_url,
        "-t", str(SCAN_SECONDS),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out),
    ]
    subprocess.run(cmd, check=True, timeout=900)
    print("X_SOURCE_ROUTE=" + route, flush=True)


def download_scan(source_url: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
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
    try:
        subprocess.run(cmd, check=True, timeout=900)
        print("X_SOURCE_ROUTE=YTDLP_DIRECT", flush=True)
    except Exception as exc:
        print(f"X_SOURCE_DIRECT_FAILED={type(exc).__name__}; trying Invidious adaptive streams", flush=True)
        out.unlink(missing_ok=True)
        _download_scan_invidious(source_url, out)
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
