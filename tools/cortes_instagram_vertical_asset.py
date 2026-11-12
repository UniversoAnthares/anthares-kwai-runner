#!/usr/bin/env python3
"""Make a verified 9:16 Instagram-only derivative without changing CORTES masters.

Cloud-hosted, bounded conversion. WordPress controls its own video storage
reservations. Deterministic derivative names avoid duplicate uploads on retry.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "https://anthares.us"
MAX_SOURCE_BYTES = 150 * 1024 * 1024
PROBE_HEADERS = "User-Agent: AntharesInstagramReels/1\r\nReferer: https://anthares.us/\r\n"


def exact_vertical(width: int, height: int) -> bool:
    return width > 0 and height > 0 and width * 16 == height * 9


def _ffmpeg_exe() -> str:
    installed = shutil.which("ffmpeg")
    if installed:
        return installed
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, OSError):
        raise RuntimeError("INSTAGRAM_FFMPEG_UNAVAILABLE") from None


def _probe(source: str | Path) -> tuple[int, int]:
    # imageio-ffmpeg bundles the encoder without ffprobe. Its stream header
    # contains the dimensions even when ffmpeg exits 1 (no output specified).
    import re
    cmd = [_ffmpeg_exe(), "-hide_banner", "-nostdin"]
    if isinstance(source, str) and source.startswith("https://"):
        cmd += ["-headers", PROBE_HEADERS]
    cmd += ["-i", str(source)]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=50)
        match = re.search(r"Video:[^\\n]*?\\b(\\d{2,5})x(\\d{2,5})\\b", run.stderr)
        if match:
            return int(match.group(1)), int(match.group(2))
    except subprocess.SubprocessError:
        pass
    raise RuntimeError("INSTAGRAM_MEDIA_DIMENSIONS_UNVERIFIED")


def _source_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or ""))
    if (parsed.scheme != "https" or parsed.hostname not in ("anthares.us", "www.anthares.us")
            or not parsed.path.lower().endswith(".mp4") or parsed.username or parsed.password
            or parsed.port or parsed.query or parsed.fragment):
        raise RuntimeError("INSTAGRAM_VERTICAL_SOURCE_INVALID")
    return url


def _auth() -> dict[str, str]:
    if os.getenv("WP_SITE_URL", "").rstrip("/") != HOST:
        raise RuntimeError("INSTAGRAM_WP_SITE_IDENTITY_INVALID")
    user = os.getenv("WP_USERNAME", "")
    password = os.getenv("WP_APP_PASSWORD", "")
    if not user or not password:
        raise RuntimeError("INSTAGRAM_WP_UPLOAD_CREDENTIAL_MISSING")
    token = base64.b64encode((user + ":" + password).encode()).decode()
    return {"Authorization": "Basic " + token, "User-Agent": "AntharesInstagramReels/1"}


def _wp_json(path: str, *, payload: dict | None = None,
             method: str = "GET", timeout: int = 45) -> dict | list:
    h = _auth()
    if payload is not None:
        h["Content-Type"] = "application/json"
    request = urllib.request.Request(HOST + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=h, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
            if isinstance(data, (dict, list)):
                return data
    except urllib.error.HTTPError as exc:
        raise RuntimeError("INSTAGRAM_WP_HTTP_" + str(exc.code)) from None
    except (OSError, ValueError):
        raise RuntimeError("INSTAGRAM_WP_UNAVAILABLE") from None
    raise RuntimeError("INSTAGRAM_WP_RESPONSE_INVALID")


def _known_dimensions(url: str, attachment_id: object) -> tuple[int, int] | None:
    if not str(attachment_id or "").isdigit():
        return None
    try:
        with urllib.request.urlopen(urllib.request.Request(
             HOST + "/wp-json/wp/v2/media/" + str(int(attachment_id)),
             headers={"User-Agent": "AntharesInstagramReels/1"}), timeout=18) as res:
            record = json.load(res)
        if record.get("source_url") != url or record.get("mime_type") != "video/mp4":
            return None
        dims = record.get("media_details") or {}
        w, h = int(dims.get("width") or 0), int(dims.get("height") or 0)
        return (w, h) if w > 0 and h > 0 else None
    except (OSError, ValueError, TypeError):
        return None


def _existing(filename: str) -> str | None:
    name = Path(filename).stem
    query = urllib.parse.urlencode({"search": name, "per_page": 50, "media_type": "video"})
    found = _wp_json("/wp-json/wp/v2/media?" + query)
    if not isinstance(found, list):
        raise RuntimeError("INSTAGRAM_WP_MEDIA_LIST_INVALID")
    for row in found:
        url = str(row.get("source_url") or "")
        if urllib.parse.urlparse(url).path.rsplit("/", 1)[-1] != filename:
            continue
        _source_url(url)
        dimensions = row.get("media_details") or {}
        w, h = int(dimensions.get("width") or 0), int(dimensions.get("height") or 0)
        if w and h and not exact_vertical(w, h):
            raise RuntimeError("INSTAGRAM_DERIVATIVE_EXISTING_RATIO_INVALID")
        return url
    return None


def _download(url: str, dst: Path) -> None:
    req = urllib.request.Request(url, headers={
        "User-Agent": "AntharesInstagramReels/1", "Referer": HOST + "/"})
    total = 0
    try:
        with urllib.request.urlopen(req, timeout=75) as response, dst.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_SOURCE_BYTES:
                    raise RuntimeError("INSTAGRAM_SOURCE_SIZE_LIMIT")
                out.write(chunk)
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("INSTAGRAM_SOURCE_DOWNLOAD_FAILED") from None
    if total < 100_000:
        raise RuntimeError("INSTAGRAM_SOURCE_TOO_SMALL")


def _render(source: Path, target: Path) -> None:
    exe = _ffmpeg_exe()
    # Preserve the full original frame in the foreground; blurred background
    # fills the exact portrait canvas without cropping speakers or book covers.
    filt = ("[0:v]split=2[fg][bg];"
            "[bg]scale=720:1280:force_original_aspect_ratio=increase,"
            "crop=720:1280,boxblur=20:1[back];"
            "[fg]scale=720:1280:force_original_aspect_ratio=decrease[front];"
            "[back][front]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    cmd = [exe, "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(source), "-filter_complex", filt, "-map", "[v]",
           "-map", "0:a:0?", "-t", "90", "-r", "30", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(target)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=420)
    except subprocess.SubprocessError:
        raise RuntimeError("INSTAGRAM_VERTICAL_RENDER_FAILED") from None
    if not exact_vertical(*_probe(target)) or target.stat().st_size < 100_000:
        raise RuntimeError("INSTAGRAM_VERTICAL_RENDER_UNVERIFIED")


def _upload(path: Path) -> str:
    size = path.stat().st_size
    if size > MAX_SOURCE_BYTES:
        raise RuntimeError("INSTAGRAM_DERIVATIVE_TOO_LARGE")
    reserve = _wp_json("/wp-json/anthares/v1/video-storage",
                       payload={"action": "reserve", "bytes": size}, method="POST", timeout=45)
    token = str(reserve.get("token") or "") if isinstance(reserve, dict) else ""
    if not token:
        raise RuntimeError("INSTAGRAM_WP_STORAGE_RESERVATION_MISSING")
    try:
        headers = _auth()
        headers.update({"Content-Disposition": 'attachment; filename="' + path.name + '"',
                        "Content-Type": "video/mp4",
                        "X-Anthares-Video-Reservation": token})
        req = urllib.request.Request(HOST + "/wp-json/wp/v2/media",
                 data=path.read_bytes(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                row = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError("INSTAGRAM_WP_UPLOAD_HTTP_" + str(exc.code)) from None
        except (OSError, ValueError):
            raise RuntimeError("INSTAGRAM_WP_UPLOAD_UNAVAILABLE") from None
        url = _source_url(str(row.get("source_url") or ""))
        if urllib.parse.urlparse(url).path.rsplit("/", 1)[-1] != path.name:
            raise RuntimeError("INSTAGRAM_DERIVATIVE_URL_MISMATCH")
        return url
    finally:
        try:
            _wp_json("/wp-json/anthares/v1/video-storage",
                     payload={"action": "release", "token": token}, method="POST", timeout=30)
        except Exception:
            print("::warning::INSTAGRAM_WP_RESERVATION_RELEASE_PENDING", flush=True)


def ensure_vertical_media(url: str, job_id: str, attachment_id: object = None) -> str:
    _source_url(url)
    dimensions = _known_dimensions(url, attachment_id)
    if dimensions is None:
        dimensions = _probe(url)
    if exact_vertical(*dimensions):
        print(json.dumps({"instagram_asset": "EXACT_9X16_VERIFIED",
                          "reencoded": False}), flush=True)
        return url
    filename = "cortes-ig9x16-" + hashlib.sha256(
        (str(job_id) + "|" + url).encode()).hexdigest()[:24] + ".mp4"
    existing = _existing(filename)
    if existing:
        if not exact_vertical(*_probe(existing)):
            raise RuntimeError("INSTAGRAM_DERIVATIVE_EXISTING_RATIO_INVALID")
        print(json.dumps({"instagram_asset": "VERTICAL_DERIVATIVE_REUSED",
                          "ratio": "9:16"}), flush=True)
        return existing
    with tempfile.TemporaryDirectory(prefix="cortes-instagram-") as temp:
        source = Path(temp) / "original.mp4"
        target = Path(temp) / filename
        _download(url, source)
        _render(source, target)
        new_url = _upload(target)
    if not exact_vertical(*_probe(new_url)):
        raise RuntimeError("INSTAGRAM_DERIVATIVE_PUBLIC_RATIO_INVALID")
    print(json.dumps({"instagram_asset": "VERTICAL_DERIVATIVE_CREATED",
                      "ratio": "9:16"}), flush=True)
    return new_url
