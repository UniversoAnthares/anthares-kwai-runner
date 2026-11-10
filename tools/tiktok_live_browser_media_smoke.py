#!/usr/bin/env python3
"""Prove cloud Chromium can receive the Anthares HLS feed as camera and microphone.

A strictly local getUserMedia smoke test, never navigates to TikTok and never
creates a LIVE. Uses a short prerecorded sample in ephemeral runner files.
"""
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading
from pathlib import Path

HLS = "https://anthares.us/wp-content/uploads/anthares-live-static/live.m3u8"

HTML = b"""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Anthares camera/microphone capability test</title><body>
<p>Test-only camera capture. No external publishing.</p></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML)
    def log_message(self, *args):
        pass

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def ffmpeg(*args):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y", *args],
                       capture_output=True, timeout=60)
    if p.returncode:
        raise RuntimeError("CLOUD_MEDIA_SAMPLE_FFMPEG_FAILED")
    return p

def main():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("CLOUD_FFMPEG_ABSENT")
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory(prefix="anthares-cloud-camera-") as tmp:
        root = Path(tmp)
        video = root / "source.y4m"
        audio = root / "source.wav"
        # 4 seconds of owned Anthares HLS; label retained in the feed.
        ffmpeg("-i", HLS, "-t", "4", "-vf",
               "fps=10,scale=360:640,drawbox=x=0:y=0:w=iw:h=60:color=black@0.95:t=fill,"
               "drawtext=text='PROGRAMA GRAVADO':fontcolor=white:fontsize=16:x=6:y=18",
               "-pix_fmt", "yuv420p", "-f", "yuv4mpegpipe", str(video))
        ffmpeg("-i", HLS, "-t", "4", "-vn", "-ac", "1", "-ar", "48000",
               "-sample_fmt", "s16", "-f", "wav", str(audio))
        if video.stat().st_size < 10000 or audio.stat().st_size < 1000:
            raise RuntimeError("CLOUD_MEDIA_SAMPLES_EMPTY")
        server = Server(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox", "--disable-dev-shm-usage",
                        "--use-fake-ui-for-media-stream",
                        "--use-fake-device-for-media-stream",
                        "--use-file-for-fake-video-capture=" + str(video),
                        "--use-file-for-fake-audio-capture=" + str(audio),
                    ],
                )
                try:
                    context = browser.new_context()
                    try:
                        context.grant_permissions(["camera", "microphone"])
                        page = context.new_page()
                        page.goto("http://127.0.0.1:" + str(server.server_port))
                        result = page.evaluate("""async()=>{
                          const stream=await navigator.mediaDevices.getUserMedia({video:true,audio:true});
                          try {
                            const video=document.createElement("video");
                            video.muted=true;video.playsInline=true;video.srcObject=stream;
                            await video.play();
                            await new Promise(r=>setTimeout(r,1600));
                            return {
                              width:video.videoWidth,height:video.videoHeight,
                              active:stream.active,
                              video:stream.getVideoTracks().map(x=>x.readyState),
                              audio:stream.getAudioTracks().map(x=>x.readyState)
                            };
                          } finally {
                            stream.getTracks().forEach(x=>x.stop());
                          }
                        }""")
                        print("CLOUD_BROWSER_MEDIA_TRACKS=" + json.dumps(result,sort_keys=True))
                        valid = (result.get("active") is True and
                                 result.get("width", 0) > 0 and
                                 result.get("height", 0) > 0 and
                                 result.get("video") == ["live"] and
                                 result.get("audio") == ["live"])
                        if not valid:
                            raise RuntimeError("CLOUD_BROWSER_MEDIA_TRACKS_INVALID")
                        print("CLOUD_BROWSER_MEDIA_SMOKE_OK=1",flush=True)
                    finally:
                        context.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        reason = str(exc)
        if not reason.startswith("CLOUD_"):
            reason = type(exc).__name__.upper()
        print("CLOUD_BROWSER_MEDIA_STATUS=" + reason[:100],flush=True)
        raise SystemExit(1)
