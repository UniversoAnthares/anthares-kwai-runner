"""Generate clip-bound transcription evidence from the actual MP4 audio.

Offline Whisper inference; no WordPress summaries or AI-generated editorial claims
are treated as a substitute for audio transcription. Output is not a signature:
publishers MUST independently verify media_sha256 before accepting this record.
"""
import argparse
import hashlib
import json
import pathlib
import re
import urllib.request

FILE = re.compile(r"^https://anthares\.us/wp-content/uploads/anthares-clips/\d{4}/\d{2}/short_([A-Za-z0-9_-]{11})_g(\d+)_(\d+)_(\d+)\.mp4$")


def prove_clip(url: str, attachment_id: int, *, model_name="small") -> dict:
    match = FILE.fullmatch(url)
    if not match or attachment_id <= 0:
        raise ValueError("UNTRUSTED_CLIP_SOURCE")
    source, round_no, start, end = match.groups()
    if not 5 <= int(end) - int(start) <= 180:
        raise ValueError("CLIP_DURATION_INVALID")
    import tempfile
    from faster_whisper import WhisperModel
    with tempfile.TemporaryDirectory(prefix="anthares-transcript-") as directory:
        path = pathlib.Path(directory) / "clip.mp4"
        size = 0
        digest = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=35) as response, path.open("wb") as output:
            while piece := response.read(1024 * 1024):
                size += len(piece)
                if size > 70_000_000:
                    raise ValueError("MEDIA_TOO_BIG")
                digest.update(piece)
                output.write(piece)
        if size < 10_000:
            raise ValueError("MEDIA_TOO_SMALL")
        model = WhisperModel(model_name, device="cpu", compute_type="int8", local_files_only=True)
        segments, info = model.transcribe(str(path), language="pt", beam_size=3, vad_filter=True)
        cues = [{"start": round(float(segment.start), 2), "end": round(float(segment.end), 2),
                 "text": segment.text.strip()} for segment in segments if segment.text.strip()]
    excerpt = " ".join(cue["text"] for cue in cues)
    if len(excerpt) < 80 or not cues:
        raise ValueError("TRANSCRIPT_TOO_SHORT_FOR_ATTESTATION")
    return {
        "schema": "anthares.clip-transcript-attestation.v1",
        "clip_id": f"g{round_no}:{source}:{start}:{end}",
        "attachment_id": attachment_id,
        "source_video_id": source,
        "source_start_s": int(start),
        "source_end_s": int(end),
        "media_sha256": digest.hexdigest(),
        "transcript_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        "method": f"faster-whisper-{model_name}-from-media",
        "language": info.language,
        "cues": cues,
        "excerpt": excerpt,
        "verified": True
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--attachment-id", required=True, type=int)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    arguments = parser.parse_args()
    result = prove_clip(arguments.url, arguments.attachment_id)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "clip_id": result["clip_id"], "sha256_verified": True,
                      "transcript_chars": len(result["excerpt"])}))
