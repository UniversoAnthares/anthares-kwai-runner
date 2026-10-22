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

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

CHANNEL_URL = os.getenv("X_SOURCE_CHANNEL", "https://www.youtube.com/@UniversoAnthares/streams")
SCAN_START = int(os.getenv("X_SCAN_START", "600"))
SCAN_SECONDS = int(os.getenv("X_SCAN_SECONDS", "780"))
MIN_SOURCE_SECONDS = int(os.getenv("X_MIN_SOURCE_SECONDS", "1800"))
WORK = Path(os.getenv("X_CLOUD_WORK", "x-cloud-work"))
MODEL = os.getenv("X_WHISPER_MODEL", "base")
INVIDIOUS_BASES = tuple(
    x.strip().rstrip("/") for x in os.getenv(
        "X_INVIDIOUS_BASES",
        "https://inv.nadeko.net,https://invidious.nerdvpn.de,https://yt.chocolatemoo53.com,https://invidious.tiekoetter.com,https://invidious.f5.si",
    ).split(",") if x.strip()
)
ITAG_HEIGHT = {160:144, 278:144, 133:240, 242:240, 134:360, 243:360, 135:480, 244:480, 136:720, 247:720, 298:720, 302:720, 137:1080, 248:1080, 299:1080, 303:1080}


def discover_source() -> dict:
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "playlistend": 300, "skip_download": True}
    cookie_path = os.getenv("X_YT_COOKIE_FILE", "").strip()
    if cookie_path and os.path.isfile(cookie_path):
        opts["cookiefile"] = cookie_path
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
    entries = list((info or {}).get("entries") or [])
    required_duration = max(MIN_SOURCE_SECONDS, SCAN_START + SCAN_SECONDS)
    windows = json.loads(os.getenv("X_SOURCE_WINDOWS_JSON", "{}"))
    if not isinstance(windows, dict):
        raise RuntimeError("X_SOURCE_WINDOWS_INVALID")
    # Canonical daily lock + persistent cursor are supplied from confirmed
    # GitHub issue history (same ledger used by all X publisher routes).
    # It is strictly forbidden to silently reset to the oldest live if the
    # prior selected source has left the 300-item discovery window.
    same_day = os.getenv("X_DAILY_LIVE_LOCK", "").strip()
    previous_day = os.getenv("X_LIVE_CURSOR_AFTER", "").strip()
    if same_day and previous_day:
        raise RuntimeError("X_SOURCE_DAILY_LOCK_CONFLICT")
    if same_day and not re.fullmatch(r"[A-Za-z0-9_-]{11}", same_day):
        raise RuntimeError("X_SOURCE_LOCK_ID_INVALID")
    if previous_day and not re.fullmatch(r"[A-Za-z0-9_-]{11}", previous_day):
        raise RuntimeError("X_SOURCE_CURSOR_INVALID")
    ordered = [entry for entry in reversed(entries) if isinstance(entry, dict)
               and re.fullmatch(r"[A-Za-z0-9_-]{11}", str(entry.get("id") or ""))]
    ids = [str(row["id"]) for row in ordered]
    if len(ids) != len(set(ids)):
        raise RuntimeError("X_SOURCE_DUPLICATE_LIVES")
    if same_day:
        if same_day not in ids:
            raise RuntimeError("X_SOURCE_DAILY_LOCK_NOT_IN_INVENTORY")
        ordered = [ordered[ids.index(same_day)]]
    elif previous_day:
        if previous_day not in ids:
            raise RuntimeError("X_SOURCE_CURSOR_NOT_IN_INVENTORY")
        ordered = ordered[ids.index(previous_day)+1:]
    # YouTube /streams returns newest-to-oldest. The CORTES editorial order
    # is the opposite: exhaust the oldest eligible live/window first, then
    # advance chronologically; previously used windows remain reserved.
    # Stable ties preserve original playlist order (latest index first).
    for e in ordered:
        if not isinstance(e, dict):
            continue
        vid = str(e.get("id") or "").strip()
        if not vid:
            continue
        live = str(e.get("live_status") or "").lower()
        duration = int(e.get("duration") or 0)
        if live in {"is_live", "is_upcoming"}:
            continue
        if not duration or duration < required_duration:
            continue
        occupied = {int(v) for v in windows.get(vid, [])}
        for index in range(16):
            candidate = SCAN_START + index * SCAN_SECONDS
            if candidate + SCAN_SECONDS <= duration and candidate not in occupied:
                return {"video_id": vid, "source_url": f"https://www.youtube.com/watch?v={vid}",
                        "title": str(e.get("title") or vid), "duration": duration,
                        "source_class": "long_form", "scan_start": candidate}
    raise RuntimeError(f"Nenhum vídeo longo concluído adequado encontrado no canal (mínimo {required_duration}s).")


def _video_id(source_url: str) -> str:
    p = urllib.parse.urlparse(source_url)
    if p.hostname in {"youtu.be", "www.youtu.be"}:
        value = p.path.strip("/")
    else:
        value = urllib.parse.parse_qs(p.query).get("v", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value or ""):
        raise RuntimeError("URL de origem do YouTube sem video id válido.")
    return value


def _itag(row: dict) -> int:
    try:
        return int(row.get("itag") or 0)
    except Exception:
        return 0


def _format_height(row: dict) -> int:
    try:
        h = int(row.get("height") or 0)
        if h:
            return h
    except Exception:
        pass
    for key in ("qualityLabel", "resolution", "quality"):
        m = re.search(r"(\d{3,4})p?", str(row.get(key) or ""))
        if m:
            return int(m.group(1))
    return ITAG_HEIGHT.get(_itag(row), 0)


def _fetch_api_formats(base: str, video_id: str) -> tuple[dict, dict]:
    url = f"{base}/api/v1/videos/{video_id}?local=false"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    adaptive = [x for x in (data.get("adaptiveFormats") or []) if isinstance(x, dict)]
    videos = [x for x in adaptive if str(x.get("type") or x.get("mimeType") or "").startswith("video/") or _format_height(x) > 0]
    audios = [x for x in adaptive if str(x.get("type") or x.get("mimeType") or "").startswith("audio/") or str(x.get("audioQuality") or "")]
    videos = [x for x in videos if _itag(x) > 0]
    audios = [x for x in audios if _itag(x) > 0]
    if not videos or not audios:
        raise RuntimeError("API sem formatos adaptativos utilizáveis")
    eligible = [x for x in videos if 0 < _format_height(x) <= 720]
    if not eligible:
        eligible = videos
    video = max(eligible, key=lambda x: (_format_height(x), int(x.get("bitrate") or 0)))
    audio = max(audios, key=lambda x: int(x.get("bitrate") or 0))
    return video, audio


def _download_scan_invidious(source_url: str, out: Path) -> None:
    video_id = _video_id(source_url)
    errors = []
    for base in INVIDIOUS_BASES:
        try:
            video, audio = _fetch_api_formats(base, video_id)
        except Exception as exc:
            errors.append(f"{base}: api {type(exc).__name__}: {str(exc)[:140]}")
            continue
        vitag, aitag = _itag(video), _itag(audio)
        height = _format_height(video)
        for local in ("true", "false"):
            out.unlink(missing_ok=True)
            vurl = f"{base}/latest_version?id={urllib.parse.quote(video_id)}&itag={vitag}&local={local}"
            aurl = f"{base}/latest_version?id={urllib.parse.quote(video_id)}&itag={aitag}&local={local}"
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-user_agent", "Mozilla/5.0",
                "-ss", str(SCAN_START), "-i", vurl,
                "-ss", str(SCAN_START), "-i", aurl,
                "-t", str(SCAN_SECONDS), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out),
            ]
            print(f"X_SOURCE_ATTEMPT base={base} local={local} vitag={vitag} aitag={aitag} height={height}", flush=True)
            try:
                subprocess.run(cmd, check=True, timeout=900, creationflags=CREATE_NO_WINDOW)
                if out.exists() and out.stat().st_size >= 100_000:
                    print(f"X_SOURCE_ROUTE=INVIDIOUS_LATEST base={base} local={local} vitag={vitag} aitag={aitag} height={height}", flush=True)
                    return
                errors.append(f"{base} local={local}: tiny output")
            except Exception as exc:
                errors.append(f"{base} local={local}: {type(exc).__name__}: {str(exc)[:140]}")
    raise RuntimeError("Invidious sem stream utilizável: " + " | ".join(errors[-12:]))


def download_scan(source_url: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    end = SCAN_START + SCAN_SECONDS
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--no-progress", "--download-sections", f"*{SCAN_START}-{end}", "--force-keyframes-at-cuts", "--merge-output-format", "mp4", "-f", "bv*[height<=720]+ba/b[height<=720]/b", "-o", str(out), source_url]
    cookie_path = os.getenv("X_YT_COOKIE_FILE", "").strip()
    if cookie_path and os.path.isfile(cookie_path):
        cmd[3:3] = ["--cookies", cookie_path]
    try:
        subprocess.run(cmd, check=True, timeout=900, creationflags=CREATE_NO_WINDOW)
        print("X_SOURCE_ROUTE=YTDLP_DIRECT", flush=True)
    except Exception as exc:
        print(f"X_SOURCE_DIRECT_FAILED={type(exc).__name__}; trying safe master mirror", flush=True)
        out.unlink(missing_ok=True)
        mirror = os.getenv("X_SOURCE_MIRROR_URL", "").strip()
        if mirror:
            if os.getenv("X_SOURCE_MIRROR_VIDEO_ID", "").strip() != _video_id(source_url):
                raise RuntimeError("X_SOURCE_MIRROR_ID_MISMATCH")
            parsed = urllib.parse.urlparse(mirror)
            if parsed.scheme != "https" or parsed.hostname not in {
                    "anthares.us", "www.anthares.us", "raw.githubusercontent.com",
                    "objects.githubusercontent.com", "github.com"}:
                raise RuntimeError("X_SOURCE_MIRROR_HOST_REJECTED")
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", str(SCAN_START), "-i", mirror, "-t", str(SCAN_SECONDS),
                    "-map", "0:v:0", "-map", "0:a:0?",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)
                ], check=True, timeout=1200, creationflags=CREATE_NO_WINDOW)
                if out.exists() and out.stat().st_size >= 100_000:
                    print("X_SOURCE_ROUTE=HOSTED_MASTER_MIRROR", flush=True)
                    return
            except Exception as mirror_exc:
                print(f"X_SOURCE_MIRROR_FAILED={type(mirror_exc).__name__}", flush=True)
                out.unlink(missing_ok=True)
        print("X_SOURCE_MIRROR_UNAVAILABLE; trying Invidious routes", flush=True)
        _download_scan_invidious(source_url, out)
    if not out.exists() or out.stat().st_size < 100_000:
        raise RuntimeError("Trecho de varredura não foi baixado corretamente.")


def probe_video(path: Path) -> dict:
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(path)], capture_output=True, text=True, check=True, timeout=30, creationflags=CREATE_NO_WINDOW)
    streams = (json.loads(p.stdout or "{}").get("streams") or [])
    if not streams:
        raise RuntimeError("Origem sem stream de vídeo.")
    width = int(streams[0].get("width") or 0); height = int(streams[0].get("height") or 0)
    if width <= 0 or height <= 0:
        raise RuntimeError("Dimensões de vídeo inválidas.")
    ratio = width / height; target = 16 / 9
    if width <= height or abs(ratio - target) > 0.04:
        raise RuntimeError(f"Origem rejeitada para X: exige horizontal 16:9; recebido {width}x{height} ({ratio:.4f}).")
    return {"width": width, "height": height, "aspect_ratio": round(ratio, 4), "format": "16:9_horizontal"}


def transcribe_words(video: Path) -> list[dict]:
    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(video), language="pt", beam_size=5, vad_filter=True, word_timestamps=True, condition_on_previous_text=True)
    words = []; idx = 0
    for seg in segments:
        for w in getattr(seg, "words", None) or []:
            text = str(getattr(w, "word", "") or "").strip(); start = float(getattr(w, "start", 0.0) or 0.0); end = float(getattr(w, "end", start) or start)
            if not text or end <= start:
                continue
            words.append({"id": idx, "s": round(start, 3), "e": round(end, 3), "t": text}); idx += 1
    if len(words) < 30:
        raise RuntimeError("Transcrição insuficiente para selecionar um corte.")
    return words


def main() -> int:
    global SCAN_START
    WORK.mkdir(parents=True, exist_ok=True)
    source = discover_source(); scan = WORK / "scan.mp4"
    SCAN_START = int(source.pop("scan_start"))
    download_scan(source["source_url"], scan)
    source["video"] = probe_video(scan)
    # Bind a reused local scan to this exact YouTube source/window. The render
    # worker may reuse this authenticated download only if the bytes still
    # match the checksum, avoiding a second 13-minute conversion.
    import hashlib
    with scan.open("rb") as existing_scan:
        digest = hashlib.file_digest(existing_scan, "sha256").hexdigest()
    (WORK / "scan.identity.json").write_text(json.dumps({
        "source_url": source["source_url"], "scan_start": SCAN_START,
        "scan_seconds": SCAN_SECONDS, "bytes": scan.stat().st_size,
        "sha256": digest,
    }, separators=(",", ":")), encoding="utf-8")
    words = transcribe_words(scan)
    payload = {
        "kind": "X_MICROCUT_REQUEST_V1", "account": "lucasyahn", "source": source,
        "scan_start": SCAN_START, "scan_seconds": SCAN_SECONDS,
        "target_seconds": {"min": 520, "max": 780},
        "output_policy": {"orientation": "horizontal", "aspect_ratio": "16:9", "source_class": "long_form"},
        "instructions": {
            "select": "Escolha um trecho autossuficiente, forte e interessante, de 520 a 780 segundos, sem intro/CTA/bastidor, somente de vídeo longo horizontal 16:9.",
            "microcut": "Dentro dele remova repetição imediata, falso começo, correção substituída, fillers/hesitações prolongadas, espaços vazios e microapartes que não integram o fluxo. Preserve argumento, nuance e gramática e garanta duração final entre 300 e 840 segundos.",
            "format": "Comente JSON X_MICROCUT_PLAN_V1 com start_word_id, end_word_id, remove [{from,to,reason}] e caption <=240 chars.",
        },
        "words": words,
    }
    Path("x-microcut-request.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("X_MICROCUT_REQUEST_READY"); print("X_SOURCE=" + source["source_url"]); print("X_SOURCE_DURATION=" + str(source["duration"])); print("X_SOURCE_FORMAT=" + json.dumps(source["video"], ensure_ascii=False, separators=(",", ":"))); print("X_WORDS=" + str(len(words)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
