#!/usr/bin/env bash
# Standalone, fail-closed Restream/TikTok live supervisor. No dependency on PC,
# Android, Kwai cron, or GitHub runner after successful bootstrap.
# Use only for a TikTok account with active, legitimate Restream authorization.
set -Eeuo pipefail
umask 077
ROOT=/home/u566597497/.anthares-tiktok-restream
FF=/home/u566597497/bin/ffmpeg-static/ffmpeg
VOD=/home/u566597497/domains/anthares.us/public_html/wp-content/uploads/anthares-live-static/vod/index.m3u8
MAX_SECONDS=21600
MIN_GOOD_SECONDS=21000
MAX_RETRIES=3
mkdir -p "$ROOT"
chmod 700 "$ROOT"
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$ROOT/supervisor.log"; }
enabled() {
  test -f "$ROOT/enabled" && test "$(cat "$ROOT/enabled")" = true
}
status() {
  if [[ -s "$ROOT/supervisor.pid" ]] && kill -0 "$(cat "$ROOT/supervisor.pid")" 2>/dev/null; then
    echo TIKTOK_HOSTINGER_SUPERVISOR=RUNNING
  else
    echo TIKTOK_HOSTINGER_SUPERVISOR=STOPPED
  fi
  if [[ -s "$ROOT/ffmpeg.pid" ]] && kill -0 "$(cat "$ROOT/ffmpeg.pid")" 2>/dev/null; then
    echo TIKTOK_HOSTINGER_FFMPEG=RUNNING
  else
    echo TIKTOK_HOSTINGER_FFMPEG=STOPPED
  fi
  if enabled; then echo TIKTOK_HOSTINGER_ENABLED=1; else echo TIKTOK_HOSTINGER_ENABLED=0; fi
}
stop_child() {
  if [[ -n "${child:-}" ]] && kill -0 "$child" 2>/dev/null; then
    kill "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
  fi
  rm -f "$ROOT/ffmpeg.pid"
}
runner() {
  test -x "$FF" && test -s "$VOD" && test -s "$ROOT/rtmp-destination" || {
    echo TIKTOK_HOSTINGER_PREFLIGHT_FAILED=1; exit 3;
  }
  enabled || { echo TIKTOK_HOSTINGER_DISARMED=1;exit 0; }
  exec 9>"$ROOT/supervisor.lock"
  flock -n 9 || { echo TIKTOK_HOSTINGER_ALREADY_RUNNING=1;exit 0; }
  echo "$$" > "$ROOT/supervisor.pid"
  trap 'stop_child; rm -f "$ROOT/supervisor.pid"; log "SUPERVISOR_STOPPED"' EXIT
  trap 'exit 0' TERM INT
  local failures=0
  while enabled; do
    # The destination is a protected file; its value is never printed or logged.
    local destination
    destination="$(cat "$ROOT/rtmp-destination")"
    case "$destination" in
      rtmp://live.restream.io/live/*|rtmps://live.restream.io/live/*) ;;
      *) log "DESTINATION_INVALID";exit 4 ;;
    esac
    [[ "$destination" != *$'\n'* ]] || exit 4
    # Avoid uncontrolled log growth and accidental storage of FFmpeg URLs.
    : > "$ROOT/ffmpeg.stderr"
    : > "$ROOT/ffmpeg.progress"
    local begun ended rc
    begun="$(date +%s)"
    (
      ulimit -c 0
      nice -n 15 "$FF" -nostdin -hide_banner -loglevel error -fflags +genpts \
        -re -i "$VOD" -t "$MAX_SECONDS" \
        -c:v copy -c:a aac -af aresample=async=1:first_pts=0,asetpts=N/SR/TB \
        -b:a 128k -ar 44100 -avoid_negative_ts make_zero \
        -f flv -progress "$ROOT/ffmpeg.progress" "$destination" \
        </dev/null >/dev/null 2>"$ROOT/ffmpeg.stderr"
    ) &
    child=$!
    echo "$child" > "$ROOT/ffmpeg.pid"
    log "CYCLE_STARTED"
    rc=0
    wait "$child" || rc=$?
    ended="$(date +%s)"
    child=""
    rm -f "$ROOT/ffmpeg.pid"
    if ! enabled; then break; fi
    if [[ "$rc" -eq 0 && $((ended-begun)) -ge "$MIN_GOOD_SECONDS" ]]; then
      failures=0
      log "CYCLE_COMPLETED"
      sleep 5
    else
      failures=$((failures+1))
      log "CYCLE_FAILED attempt=$failures"
      if (( failures >= MAX_RETRIES )); then
        echo false > "$ROOT/enabled"
        log "CIRCUIT_BREAKER_OPEN"
        break
      fi
      sleep 120
    fi
  done
  echo TIKTOK_HOSTINGER_LOOP_EXITED=1
}
case "${1:-}" in
  run) runner ;;
  status) status ;;
  stop)
    echo false > "$ROOT/enabled"
    if [[ -s "$ROOT/supervisor.pid" ]]; then
      pid="$(cat "$ROOT/supervisor.pid")"
      [[ "$pid" =~ ^[0-9]+$ ]] && kill "$pid" 2>/dev/null || true
    fi
    echo TIKTOK_HOSTINGER_STOP_REQUESTED=1
    ;;
  start)
    test -s "$ROOT/rtmp-destination" || { echo TIKTOK_HOSTINGER_SECRET_MISSING=1;exit 4; }
    echo true > "$ROOT/enabled"
    nohup bash "$0" run </dev/null >/dev/null 2>&1 &
    sleep 3
    status
    ;;
  *) echo 'USAGE: start|stop|status|run'; exit 2 ;;
esac
