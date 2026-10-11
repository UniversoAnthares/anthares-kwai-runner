#!/usr/bin/env bash
set -Eeuo pipefail

YOUTUBE_URL="${YOUTUBE_URL:?YOUTUBE_URL is required}"
X_RTMP_URL="${X_RTMP_URL:?X_RTMP_URL is required}"
X_RTMP_STREAM_KEY="${X_RTMP_STREAM_KEY:?X_RTMP_STREAM_KEY is required}"
VIDEO_HEIGHT="${VIDEO_HEIGHT:-720}"
VIDEO_FPS="${VIDEO_FPS:-30}"
VIDEO_BITRATE="${VIDEO_BITRATE:-4500k}"
AUDIO_BITRATE="${AUDIO_BITRATE:-128k}"

command -v yt-dlp >/dev/null 2>&1 || { echo "yt-dlp is required" >&2; exit 2; }
command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg is required" >&2; exit 2; }

# Resolve the current live media URL at runtime. yt-dlp handles YouTube's signed live manifests.
INPUT_URL="$(yt-dlp --no-warnings --no-playlist -f 'best[height<=1080]/best' -g "$YOUTUBE_URL" | head -n 1)"
if [[ -z "$INPUT_URL" ]]; then
  echo "Unable to resolve an active YouTube live stream." >&2
  exit 3
fi

DEST="${X_RTMP_URL%/}/${X_RTMP_STREAM_KEY}"

# X Producer requires a separate stream. Re-encode to a conservative X-compatible profile:
# H.264 + AAC-LC, 720p/30, keyframes every 3 seconds.
exec ffmpeg \
  -hide_banner -loglevel info \
  -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 \
  -i "$INPUT_URL" \
  -map 0:v:0 -map 0:a:0? \
  -vf "scale=-2:${VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2" \
  -r "$VIDEO_FPS" \
  -c:v libx264 -preset veryfast -profile:v high -level 4.1 \
  -b:v "$VIDEO_BITRATE" -maxrate "$VIDEO_BITRATE" -bufsize 9000k \
  -g $((VIDEO_FPS * 3)) -keyint_min $((VIDEO_FPS * 3)) -sc_threshold 0 \
  -c:a aac -b:a "$AUDIO_BITRATE" -ar 48000 -ac 2 \
  -f flv "$DEST"
