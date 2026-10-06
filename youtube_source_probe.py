#!/usr/bin/env python3
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import threading
import time
from flask import Flask, jsonify, request

app = Flask(__name__)

ALLOWED_IDS = {
    "a4w8KAOxANc",
    "f8eilImtDug",
    "68tVYgXmoRI",
    "uohL105_5bg",
    "otvyyx2x-fE",
}
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _direct_watch_probe(video_id: str) -> dict:
    q = urllib.parse.urlencode({
        "v": video_id,
        "hl": "pt-BR",
        "gl": "BR",
        "bpctr": "9999999999",
        "has_verified": "1",
    })
    req = urllib.request.Request(
        "https://www.youtube.com/watch?" + q,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/154.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read(2_000_000)
            text = raw.decode("utf-8", "replace")
            return {
                "http": int(getattr(r, "status", 200)),
                "bytes_sampled": len(raw),
                "bot_phrase": "confirm you" in text.lower() or "not a bot" in text.lower(),
                "has_caption_tracks_marker": "captionTracks" in text,
                "has_player_response_marker": "ytInitialPlayerResponse" in text,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(4096).decode("utf-8", "replace")
        return {
            "http": int(exc.code),
            "bytes_sampled": len(body.encode("utf-8", "replace")),
            "bot_phrase": "confirm you" in body.lower() or "not a bot" in body.lower(),
            "error": "HTTPError",
        }
    except Exception as exc:
        return {"error": type(exc).__name__}


def _ydl_probe(video_id: str, client: str | None) -> dict:
    try:
        import yt_dlp
    except Exception as exc:
        return {"ok": False, "error": "yt_dlp_import", "type": type(exc).__name__}

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 0,
        "extractor_retries": 0,
    }
    if client:
        opts["extractor_args"] = {"youtube": {"player_client": [client]}}

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        if not isinstance(info, dict):
            return {"ok": False, "error": "invalid_info"}

        formats = [x for x in (info.get("formats") or []) if isinstance(x, dict)]
        audio = [x for x in formats if str(x.get("vcodec") or "") == "none" and str(x.get("acodec") or "") not in ("", "none")]
        direct_audio = [x for x in audio if bool(x.get("url"))]
        subtitles = info.get("subtitles") if isinstance(info.get("subtitles"), dict) else {}
        automatic = info.get("automatic_captions") if isinstance(info.get("automatic_captions"), dict) else {}
        return {
            "ok": True,
            "id": str(info.get("id") or ""),
            "title": str(info.get("title") or "")[:300],
            "duration": info.get("duration"),
            "live_status": info.get("live_status"),
            "was_live": bool(info.get("was_live")),
            "format_count": len(formats),
            "audio_format_count": len(audio),
            "direct_audio_count": len(direct_audio),
            "subtitle_languages": sorted(str(k) for k in subtitles.keys())[:50],
            "automatic_caption_languages": sorted(str(k) for k in automatic.keys())[:80],
            "has_pt_caption": any(str(k).lower().startswith("pt") for k in list(subtitles.keys()) + list(automatic.keys())),
        }
    except Exception as exc:
        msg = re.sub(r"https?://\S+", "<url>", str(exc))
        return {
            "ok": False,
            "error": type(exc).__name__,
            "message": msg[:800],
        }


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "anthares-youtube-source-probe", "mode": "read-only"})


@app.get("/probe")
def probe():
    video_id = str(request.args.get("id") or "").strip()
    client = str(request.args.get("client") or "").strip() or None
    if not VIDEO_ID_RE.fullmatch(video_id) or video_id not in ALLOWED_IDS:
        return jsonify({"ok": False, "error": "video_id_not_allowed"}), 400
    if client and client not in {"android_vr", "tv", "web_safari", "mweb", "default"}:
        return jsonify({"ok": False, "error": "client_not_allowed"}), 400
    if client == "default":
        client = None
    return jsonify({
        "ok": True,
        "video_id": video_id,
        "client": client or "default",
        "direct_watch": _direct_watch_probe(video_id),
        "yt_dlp": _ydl_probe(video_id, client),
    })


def _startup_probe():
    time.sleep(8)
    video_id = os.environ.get("PROBE_VIDEO_ID", "uohL105_5bg").strip()
    clients = ["default", "android_vr", "tv", "web_safari", "mweb"]
    for raw_client in clients:
        client = None if raw_client == "default" else raw_client
        result = {
            "event": "STARTUP_SOURCE_PROBE",
            "video_id": video_id,
            "client": raw_client,
            "direct_watch": _direct_watch_probe(video_id),
            "yt_dlp": _ydl_probe(video_id, client),
        }
        print(json.dumps(result, ensure_ascii=False), flush=True)


threading.Thread(target=_startup_probe, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
