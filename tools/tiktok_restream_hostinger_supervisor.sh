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
  local sup="" childpid="" mtime=0 now=0
  [[ -s "$ROOT/supervisor.pid" ]] && sup="$(cat "$ROOT/supervisor.pid")"
  [[ -s "$ROOT/ffmpeg.pid" ]] && childpid="$(cat "$ROOT/ffmpeg.pid")"
  if process_is_ours "$sup" "$ROOT/supervisor.sh"; then
    echo TIKTOK_HOSTINGER_SUPERVISOR=RUNNING
    local sid=""
    sid="$(ps -p "$sup" -o sid= 2>/dev/null | tr -d ' ')"
    if [[ "$sid" = "$sup" ]]; then
      echo TIKTOK_HOSTINGER_SESSION_ISOLATED=1
    else
      echo TIKTOK_HOSTINGER_SESSION_ISOLATED=0
    fi
  else
    echo TIKTOK_HOSTINGER_SUPERVISOR=STOPPED
  fi
  if tiktok_child_is_ours "$childpid" "$sup"; then
    now="$(date +%s)"
    mtime="$(stat -c %Y "$ROOT/ffmpeg.progress" 2>/dev/null || echo 0)"
    if ((mtime>0 && now-mtime<=420)); then
      echo TIKTOK_HOSTINGER_FFMPEG=RUNNING
    else
      echo TIKTOK_HOSTINGER_FFMPEG=STALLED
    fi
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
    # Start FFmpeg directly so $! is the encoder PID, not a Bash wrapper.
    ulimit -c 0
    nice -n 15 "$FF" -nostdin -hide_banner -loglevel error -fflags +genpts \
      -re -i "$VOD" -t "$MAX_SECONDS" \
      -c:v copy -c:a aac -af aresample=async=1:first_pts=0,asetpts=N/SR/TB \
      -b:a 128k -ar 44100 -avoid_negative_ts make_zero \
      -f flv -progress "$ROOT/ffmpeg.progress" "$destination" \
      </dev/null >/dev/null 2>"$ROOT/ffmpeg.stderr" &
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
# Called by an independent scheduler. It never enables a disarmed transmitter.
# A stale supervisor may have been killed by shared hosting outside Bash traps.
process_is_ours() {
  local pid="${1:-}" needle="${2:-}"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  [[ -r "/proc/$pid/cmdline" ]] || return 1
  tr '\0' ' ' < "/proc/$pid/cmdline" | grep -Fq -- "$needle"
}
tiktok_child_is_ours() {
  local childpid="${1:-}" supervisorpid="${2:-}" ppid=""
  process_is_ours "$childpid" "$ROOT/ffmpeg.progress" && return 0
  # The recorded $! PID belongs to a Bash subshell; ffmpeg is its child.
  # Only accept it if the process belongs to this script and is parented
  # by the expected supervisor. An orphan is accepted solely for cleanup.
  process_is_ours "$childpid" "$ROOT/supervisor.sh" || return 1
  [[ "$supervisorpid" =~ ^[0-9]+$ ]] || return 1
  ppid="$(ps -p "$childpid" -o ppid= 2>/dev/null | tr -d ' ')"
  [[ "$ppid" = "$supervisorpid" || "$ppid" = 1 ]]
}
launch_detached() {
  command -v setsid >/dev/null || { log "SETSID_MISSING"; return 6; }
  setsid -f nohup bash "$ROOT/supervisor.sh" run </dev/null >/dev/null 2>&1
}
watchdog_tick() {
  enabled || { echo TIKTOK_WATCHDOG_DISARMED=1; return 0; }
  test -s "$ROOT/rtmp-destination" || {
    log "WATCHDOG_NO_CREDENTIAL"; echo TIKTOK_WATCHDOG_MISSING_SECRET=1; return 3;
  }
  exec 8>"$ROOT/watchdog.lock"
  flock -n 8 || { echo TIKTOK_WATCHDOG_LOCK_BUSY=1; return 0; }
  # Observable receipt for a native hPanel cron invocation, never a credential.
  date -u +%FT%TZ > "$ROOT/watchdog-last-tick"
  local sup="" childpid="" now=0 mtime=0
  [[ -s "$ROOT/supervisor.pid" ]] && sup="$(cat "$ROOT/supervisor.pid")"
  [[ -s "$ROOT/ffmpeg.pid" ]] && childpid="$(cat "$ROOT/ffmpeg.pid")"
  if process_is_ours "$sup" "$ROOT/supervisor.sh"; then
    # Normal handovers and supervised two-minute backoff are respected.
    # Do not interfere with a working Kwai or TikTok stream.
    if tiktok_child_is_ours "$childpid" "$sup"; then
      now="$(date +%s)"
      mtime="$(stat -c %Y "$ROOT/ffmpeg.progress" 2>/dev/null || echo 0)"
      if (( mtime > 0 && now-mtime > 420 )); then
        log "WATCHDOG_STALLED_PROTECTED_TIKTOK"
        kill -TERM "$sup" 2>/dev/null || true
        sleep 4
      else
        echo TIKTOK_WATCHDOG_HEALTHY=1
        return 0
      fi
    else
      # Parent owns retry policy; do not prematurely reset fail counter.
      echo TIKTOK_WATCHDOG_SUPERVISOR_RETRYING=1
      return 0
    fi
  fi
  # If any previously orphaned transcoder still owns TikTok progress,
  # stop only that exact process. Do not touch the Kwai PID or files.
  if tiktok_child_is_ours "$childpid" "$sup"; then
    log "WATCHDOG_TIKTOK_ORPHAN_FOUND"
    kill -TERM "$childpid" 2>/dev/null || true
    sleep 3
    if tiktok_child_is_ours "$childpid" "$sup"; then
      log "WATCHDOG_TIKTOK_ORPHAN_STILL_ALIVE"
      echo TIKTOK_WATCHDOG_ORPHAN_BLOCKED=1
      return 5
    fi
  fi
  log "WATCHDOG_RESTARTING"
  launch_detached
  sleep 3
  if [[ -s "$ROOT/supervisor.pid" ]] && process_is_ours "$(cat "$ROOT/supervisor.pid")" "$ROOT/supervisor.sh"; then
    echo TIKTOK_WATCHDOG_RESTARTED=1
  else
    log "WATCHDOG_RESTART_UNCONFIRMED"
    echo TIKTOK_WATCHDOG_RESTART_UNCONFIRMED=1
    return 4
  fi
}
case "${1:-}" in
  run) runner ;;
  tick) watchdog_tick ;;
  status) status ;;
  stop)
    echo false > "$ROOT/enabled"
    if [[ -s "$ROOT/supervisor.pid" ]]; then
      pid="$(cat "$ROOT/supervisor.pid")"
      process_is_ours "$pid" "$ROOT/supervisor.sh" && kill "$pid" 2>/dev/null || true
    fi
    echo TIKTOK_HOSTINGER_STOP_REQUESTED=1
    ;;
  start)
    test -s "$ROOT/rtmp-destination" || { echo TIKTOK_HOSTINGER_SECRET_MISSING=1;exit 4; }
    echo true > "$ROOT/enabled"
    launch_detached
    sleep 3
    status
    ;;
  *) echo 'USAGE: start|stop|status|run|tick'; exit 2 ;;
esac
