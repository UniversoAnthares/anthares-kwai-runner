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

# Prefer separate best video + audio when YouTube exposes adaptive live formats,
# with a muxed fallback. Signed media URLs are resolved only at runtime.
mapfile -t INPUT_URLS < <(
  yt-dlp --no-warnings --no-playlist \
    -f 'bv*[height<=1080]+ba/b[height<=1080]/b' \
    -g "$YOUTUBE_URL"
)

if (( ${#INPUT_URLS[@]} == 0 )); then
  echo "Unable to resolve an active YouTube live stream." >&2
  exit 3
fi

DEST="${X_RTMP_URL%/}/${X_RTMP_STREAM_KEY}"

COMMON_INPUT=(
  -reconnect 1
  -reconnect_streamed 1
  -reconnect_delay_max 5
)

if (( ${#INPUT_URLS[@]} >= 2 )); then
  INPUT_ARGS=("${COMMON_INPUT[@]}" -i "${INPUT_URLS[0]}" "${COMMON_INPUT[@]}" -i "${INPUT_URLS[1]}")
  MAP_ARGS=(-map 0:v:0 -map 1:a:0)
else
  INPUT_ARGS=("${COMMON_INPUT[@]}" -i "${INPUT_URLS[0]}")
  MAP_ARGS=(-map 0:v:0 -map 0:a:0?)
fi

# X Producer requires a dedicated stream. Re-encode to an X-compatible profile:
# H.264/AVC + AAC-LC, 720p or 1080p, with a 3-second keyframe interval.
exec ffmpeg \
  -hide_banner -loglevel warning \
  "${INPUT_ARGS[@]}" \
  "${MAP_ARGS[@]}" \
  -vf "scale=-2:${VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2" \
  -r "$VIDEO_FPS" \
  -c:v libx264 -preset veryfast -profile:v high -level 4.1 \
  -b:v "$VIDEO_BITRATE" -maxrate "$VIDEO_BITRATE" -bufsize 9000k \
  -g $((VIDEO_FPS * 3)) -keyint_min $((VIDEO_FPS * 3)) -sc_threshold 0 \
  -c:a aac -b:a "$AUDIO_BITRATE" -ar 48000 -ac 2 \
  -f flv "$DEST"
