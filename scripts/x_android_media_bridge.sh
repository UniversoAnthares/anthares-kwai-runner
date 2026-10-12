#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-}"
VIDEO_DEVICE="${VIDEO_DEVICE:-/dev/video10}"
VIDEO_NR="${VIDEO_NR:-10}"
PULSE_SINK="${PULSE_SINK:-anthares_x_live}"
WORK_DIR="${WORK_DIR:-/tmp/anthares-x-live}"
SOURCE_URL="${SOURCE_URL:-}"
WIDTH="${WIDTH:-1280}"
HEIGHT="${HEIGHT:-720}"
FPS="${FPS:-30}"

mkdir -p "$WORK_DIR"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing dependency: $1" >&2; exit 2; }
}

pulse_start() {
  if ! pactl info >/dev/null 2>&1; then
    pulseaudio --start --exit-idle-time=-1 >/dev/null 2>&1 || true
    sleep 1
  fi
  pactl info >/dev/null
}

pulse_prepare() {
  pulse_start
  if ! pactl list short sinks | awk '{print $2}' | grep -Fxq "$PULSE_SINK"; then
    pactl load-module module-null-sink sink_name="$PULSE_SINK" sink_properties=device.description=Anthares_X_Live >/dev/null
  fi
  pactl set-default-source "${PULSE_SINK}.monitor"
}

video_prepare() {
  need v4l2-ctl
  if [[ ! -e "$VIDEO_DEVICE" ]]; then
    sudo modprobe -r v4l2loopback >/dev/null 2>&1 || true
    # Keep capture+output capabilities visible before FFmpeg attaches, so the
    # Android Emulator can enumerate webcam0 during its own startup probe.
    sudo modprobe v4l2loopback devices=1 video_nr="$VIDEO_NR" card_label="Anthares X Live" exclusive_caps=0
  fi
  sudo chmod 666 "$VIDEO_DEVICE"
  v4l2-ctl -d "$VIDEO_DEVICE" --all >/dev/null
}

resolve_youtube() {
  need yt-dlp
  mapfile -t URLS < <(yt-dlp --no-warnings --no-playlist -f 'bestvideo[height<=1080]+bestaudio/best[height<=1080]' -g "$SOURCE_URL")
  VIDEO_URL="${URLS[0]:-}"
  AUDIO_URL="${URLS[1]:-${URLS[0]:-}}"
  [[ -n "$VIDEO_URL" ]] || { echo "unable to resolve an active YouTube live video" >&2; exit 3; }
}

start_video() {
  need ffmpeg
  if [[ -n "$SOURCE_URL" ]]; then
    resolve_youtube
    nohup ffmpeg -nostdin -hide_banner -loglevel warning \
      -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 \
      -i "$VIDEO_URL" \
      -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps=${FPS},format=yuyv422" \
      -pix_fmt yuyv422 -f v4l2 "$VIDEO_DEVICE" \
      >"$WORK_DIR/video.log" 2>&1 &
  else
    nohup ffmpeg -nostdin -hide_banner -loglevel warning \
      -re -f lavfi -i "testsrc2=size=${WIDTH}x${HEIGHT}:rate=${FPS}" \
      -vf "format=yuyv422" -pix_fmt yuyv422 -f v4l2 "$VIDEO_DEVICE" \
      >"$WORK_DIR/video.log" 2>&1 &
  fi
  echo $! >"$WORK_DIR/video.pid"
}

start_audio() {
  need ffmpeg
  pulse_prepare
  if [[ -n "$SOURCE_URL" ]]; then
    [[ -n "${AUDIO_URL:-}" ]] || resolve_youtube
    nohup ffmpeg -nostdin -hide_banner -loglevel warning \
      -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 \
      -i "$AUDIO_URL" -vn -ac 2 -ar 48000 -f pulse "$PULSE_SINK" \
      >"$WORK_DIR/audio.log" 2>&1 &
  else
    nohup ffmpeg -nostdin -hide_banner -loglevel warning \
      -re -f lavfi -i "sine=frequency=523.25:sample_rate=48000" \
      -ac 2 -ar 48000 -f pulse "$PULSE_SINK" \
      >"$WORK_DIR/audio.log" 2>&1 &
  fi
  echo $! >"$WORK_DIR/audio.pid"
}

stop_all() {
  for f in "$WORK_DIR/video.pid" "$WORK_DIR/audio.pid"; do
    if [[ -s "$f" ]]; then
      pid="$(cat "$f")"
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" >/dev/null 2>&1 || true
      rm -f "$f"
    fi
  done
}

verify() {
  need ffmpeg
  [[ -e "$VIDEO_DEVICE" ]] || { echo "video bridge missing: $VIDEO_DEVICE" >&2; exit 4; }
  for f in "$WORK_DIR/video.pid" "$WORK_DIR/audio.pid"; do
    [[ -s "$f" ]] || { echo "missing pid file: $f" >&2; exit 4; }
    kill -0 "$(cat "$f")" || { echo "bridge process exited: $f" >&2; exit 4; }
  done
  timeout 8 ffmpeg -hide_banner -loglevel error -f v4l2 -framerate "$FPS" -video_size "${WIDTH}x${HEIGHT}" -i "$VIDEO_DEVICE" -frames:v 3 -f null -
  pulse_start
  pactl list short sources | grep -F "${PULSE_SINK}.monitor" >/dev/null
  echo "BRIDGE_OK video=$VIDEO_DEVICE source=${PULSE_SINK}.monitor ${WIDTH}x${HEIGHT}@${FPS}"
}

case "$MODE" in
  prepare)
    need pactl
    need pulseaudio
    video_prepare
    pulse_prepare
    ;;
  start)
    video_prepare
    pulse_prepare
    stop_all
    start_video
    start_audio
    sleep 3
    verify
    ;;
  verify)
    verify
    ;;
  stop)
    stop_all
    ;;
  *)
    echo "usage: $0 {prepare|start|verify|stop}" >&2
    exit 2
    ;;
esac
