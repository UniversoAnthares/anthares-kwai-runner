#!/usr/bin/env python3
import base64
import json
import os
import pathlib
import re
import shutil
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from flask import Flask, jsonify, request

app = Flask(__name__)

ALLOWED_IDS = {
    "a4w8KAOxANc", "f8eilImtDug", "68tVYgXmoRI", "uohL105_5bg",
    "otvyyx2x-fE", "HtRVqkQ5Opo",
}
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
COOKIE_FILE = pathlib.Path("/tmp/anthares-youtube-cookies.txt")
AUTH_STATE = {"configured": False, "metadata": "pending", "full_acquisition": "pending", "source_deleted": False}


def _materialize_cookie_secret() -> str | None:
    encoded = os.environ.get("YOUTUBE_COOKIES_B64", "").strip()
    raw = os.environ.get("YOUTUBE_COOKIES", "")
    if encoded:
        try:
            data = base64.b64decode(encoded, validate=True)
        except Exception:
            AUTH_STATE["metadata"] = "cookie_secret_invalid_base64"
            return None
        COOKIE_FILE.write_bytes(data)
    elif raw.strip():
        COOKIE_FILE.write_text(raw, encoding="utf-8")
    else:
        return None
    os.chmod(COOKIE_FILE, 0o600)
    AUTH_STATE["configured"] = True
    return str(COOKIE_FILE)


def _direct_watch_probe(video_id: str) -> dict:
    q = urllib.parse.urlencode({"v": video_id, "hl": "pt-BR", "gl": "BR", "bpctr": "9999999999", "has_verified": "1"})
    req = urllib.request.Request(
        "https://www.youtube.com/watch?" + q,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/154.0.0.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read(2_000_000)
            text = raw.decode("utf-8", "replace")
            return {"http": int(getattr(r, "status", 200)), "bytes_sampled": len(raw), "bot_phrase": "confirm you" in text.lower() or "not a bot" in text.lower(), "has_caption_tracks_marker": "captionTracks" in text, "has_player_response_marker": "ytInitialPlayerResponse" in text}
    except urllib.error.HTTPError as exc:
        body = exc.read(4096).decode("utf-8", "replace")
        return {"http": int(exc.code), "bytes_sampled": len(body.encode("utf-8", "replace")), "bot_phrase": "confirm you" in body.lower() or "not a bot" in body.lower(), "error": "HTTPError"}
    except Exception as exc:
        return {"error": type(exc).__name__}


def _ydl_opts(skip_download=True) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": skip_download, "noplaylist": True, "socket_timeout": 45, "retries": 2, "extractor_retries": 2}
    cookie = _materialize_cookie_secret()
    if cookie:
        opts["cookiefile"] = cookie
    return opts


def _ydl_probe(video_id: str, client: str | None) -> dict:
    try:
        import yt_dlp
    except Exception as exc:
        return {"ok": False, "error": "yt_dlp_import", "type": type(exc).__name__}
    opts = _ydl_opts(True)
    if client:
        opts["extractor_args"] = {"youtube": {"player_client": [client]}}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        if not isinstance(info, dict):
            return {"ok": False, "error": "invalid_info"}
        formats = [x for x in (info.get("formats") or []) if isinstance(x, dict)]
        return {"ok": True, "id": str(info.get("id") or ""), "title": str(info.get("title") or "")[:300], "duration": info.get("duration"), "live_status": info.get("live_status"), "was_live": bool(info.get("was_live")), "format_count": len(formats), "authenticated": bool(AUTH_STATE["configured"])}
    except Exception as exc:
        msg = re.sub(r"https?://\S+", "<url>", str(exc))
        return {"ok": False, "error": type(exc).__name__, "message": msg[:500], "authenticated": bool(AUTH_STATE["configured"])}


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "anthares-youtube-source-probe", "mode": "authenticated-remote-executor", "youtube_auth": AUTH_STATE})


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
    return jsonify({"ok": True, "video_id": video_id, "client": client or "default", "direct_watch": _direct_watch_probe(video_id), "yt_dlp": _ydl_probe(video_id, client)})


def _authenticated_full_acquisition_probe():
    time.sleep(6)
    video_id = os.environ.get("AUTH_TEST_VIDEO_ID", "HtRVqkQ5Opo").strip()
    if not _materialize_cookie_secret():
        AUTH_STATE["metadata"] = "cookie_secret_missing"
        AUTH_STATE["full_acquisition"] = "not_run"
        print("YOUTUBE_REMOTE_AUTH=COOKIE_SECRET_MISSING", flush=True)
        return
    try:
        import yt_dlp
        meta = _ydl_probe(video_id, None)
        if not meta.get("ok") or float(meta.get("duration") or 0) < 300:
            raise RuntimeError("authenticated metadata probe failed")
        AUTH_STATE["metadata"] = "proven"
        print(f"YOUTUBE_REMOTE_AUTH=METADATA_PROVEN id={video_id} duration={float(meta['duration']):.3f}", flush=True)
        root = pathlib.Path("/tmp/anthares-auth-full")
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        opts = _ydl_opts(False)
        opts.update({"format": "18/best[height<=720]/best", "outtmpl": str(root / "source.%(ext)s")})
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            downloaded = pathlib.Path(ydl.prepare_filename(info))
        candidates = [p for p in root.glob("source.*") if p.is_file()]
        if not candidates and downloaded.is_file():
            candidates = [downloaded]
        if not candidates:
            raise RuntimeError("full source file missing")
        source = max(candidates, key=lambda p: p.stat().st_size)
        size = source.stat().st_size
        duration = float((info or {}).get("duration") or 0)
        if size < 5_000_000 or duration < 300:
            raise RuntimeError(f"full source validation failed size={size} duration={duration}")
        AUTH_STATE["full_acquisition"] = "proven"
        print(f"YOUTUBE_REMOTE_AUTH=FULL_ACQUISITION_PROVEN id={video_id} bytes={size} duration={duration:.3f}", flush=True)
        shutil.rmtree(root, ignore_errors=True)
        AUTH_STATE["source_deleted"] = not root.exists()
        print("YOUTUBE_REMOTE_AUTH=SOURCE_DELETED_AFTER_PROBE", flush=True)
    except Exception as exc:
        AUTH_STATE["full_acquisition"] = "failed:" + type(exc).__name__
        print("YOUTUBE_REMOTE_AUTH=FAILED type=" + type(exc).__name__, flush=True)
    finally:
        COOKIE_FILE.unlink(missing_ok=True)


threading.Thread(target=_authenticated_full_acquisition_probe, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
