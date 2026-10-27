#!/usr/bin/env python3
"""One-shot remote editorial evidence job. No publishing, no local-PC staging."""
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from faster_whisper import WhisperModel

VIDEO_ID = "fOmihuHUT1M"
START = 668
END = 708
CLIP = f"g1:{VIDEO_ID}:{START}:{END}"
NAME = f"short_{VIDEO_ID}_g1_{START}_{END}.mp4"
URL = f"https://anthares.us/wp-content/uploads/anthares-clips/2026/10/{NAME}"
EXPECTED = "35cab02c13f525bbf1573cf91ce69bde2bde4b77fdf33856af415d96a7b6613a"

def read_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Anthares-Cloud-ASR-Checksum/1.0"})
    with urllib.request.urlopen(req, timeout=35) as resp:
        return json.load(resp)

def main():
    query = urllib.parse.urlencode({"search": NAME.removesuffix(".mp4"), "per_page": "30"})
    media_index = read_json("https://anthares.us/wp-json/wp/v2/media?" + query)
    matches = [row for row in media_index if row.get("source_url") == URL and row.get("mime_type") == "video/mp4"]
    if len(matches) != 1:
        raise RuntimeError(f"WORDPRESS_ATTACHMENT_NOT_UNIQUE count={len(matches)}")
    attachment_id = int(matches[0]["id"])
    with tempfile.TemporaryDirectory(prefix="anthares-asr-cloud-") as tmp:
        video_path = Path(tmp) / "source.mp4"
        digest = hashlib.sha256()
        total = 0
        req = urllib.request.Request(URL, headers={"User-Agent": "Anthares-Cloud-ASR-Checksum/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp, video_path.open("wb") as out:
            while chunk := resp.read(1024 * 1024):
                total += len(chunk)
                if total > 70_000_000:
                    raise RuntimeError("MEDIA_TOO_LARGE")
                digest.update(chunk)
                out.write(chunk)
        actual = digest.hexdigest()
        if actual != EXPECTED:
            raise RuntimeError(f"MEDIA_SHA256_DIFFERS_NEON expected={EXPECTED} actual={actual}")
        if total < 10000:
            raise RuntimeError("MEDIA_TOO_SMALL")
        model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
        segments, _info = model.transcribe(
            str(video_path), language="pt", beam_size=3,
            vad_filter=True, condition_on_previous_text=False, temperature=0,
        )
        cues = []
        for seg in segments:
            segment_text = seg.text.strip()
            if segment_text and seg.end > seg.start:
                cues.append({"start": round(float(seg.start), 2),
                             "end": round(float(seg.end), 2),
                             "text": segment_text})
        excerpt = " ".join(cue["text"] for cue in cues)
        if len(excerpt) < 60:
            raise RuntimeError("EDITORIAL_TRANSCRIPT_TOO_SHORT")
        if any(cue["end"] > (END - START) + 5 for cue in cues):
            raise RuntimeError("EDITORIAL_TIMECODES_OUT_OF_RANGE")
        evidence = {
            "schema": "anthares.clip-transcript-attestation.v1",
            "clip_id": CLIP,
            "attachment_id": attachment_id,
            "source_video_id": VIDEO_ID,
            "source_start_s": START,
            "source_end_s": END,
            "media_sha256": actual,
            "method": "faster-whisper-small-from-media",
            "language": "pt",
            "cues": cues,
            "excerpt": excerpt,
            "verified": True,
        }
        output = Path(os.environ["GITHUB_WORKSPACE"]) / "threads-668-708-evidence.json"
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        proof = base64.b64encode(json.dumps(evidence, ensure_ascii=False, separators=(",", ":")).encode()).decode()
        print(f"ASR_VERIFIED clip={CLIP} attachment={attachment_id} sha256={actual} bytes={total} cues={len(cues)} chars={len(excerpt)}", flush=True)
        print(f"EVIDENCE_JSON_BASE64={proof}", flush=True)

if __name__ == "__main__":
    main()
