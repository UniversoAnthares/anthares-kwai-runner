#!/usr/bin/env bash
set -euo pipefail

: "${VNC_PASSWORD:?VNC_PASSWORD is required}"
: "${CONTROL_TOKEN:?CONTROL_TOKEN is required}"

export DISPLAY=${DISPLAY:-:99}
export CHROME_PROFILE_DIR=${CHROME_PROFILE_DIR:-/data/chrome-profile}
START_URL=${START_URL:-about:blank}
CDP_PORT=${CDP_PORT:-9222}
API_PORT=${PORT:-8080}
export NO_PROXY="127.0.0.1,localhost,::1${NO_PROXY:+,$NO_PROXY}"
export no_proxy="127.0.0.1,localhost,::1${no_proxy:+,$no_proxy}"
mkdir -p "$CHROME_PROFILE_DIR" /run/anthares-brouser

API_PID=""
XVFB_PID=""
VNC_PID=""
NOVNC_PID=""
CHROME_PID=""

log() {
  printf '[anthares-browser] %s\n' "$*"
}

stop_pid() {
  local pid="${1:-}"
  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 32); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.25
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "$pid" 2>/dev/null || true
  fi
  wait "$pid" 2>/dev/null || true
}

cleanup() {
  stop_pid "$CHROME_PID"
  if [[ "${GITLAB_STATE_ENABLED:-0}" == "1" ]]; then
    python /opt/anthares-brouser/profile_store.py backup || log "encrypted snapshot backup failed"
  fi
  stop_pid "$NOVNC_PID"
  stop_pid "$VNC_PID"
  stop_pid "$XVFB_PID"
  stop_pid "$API_PID"
}

shutdown() {
  log "shutdown requested; stopping isolated browser stack"
  trap - EXIT INT TERM
  cleanup
  exit 0
}

trap cleanup EXIT
trap shutdown INT TERM

start_api() {
  log "starting control API on 0.0.0.0:${API_PORT}"
  uvicorn app:app --host 0.0.0.0 --port "$API_PORT" --app-dir /opt/anthares-brouser --no-access-log &
  API_PID=$!
}

wait_api_health() {
  for _ in $(seq 1 150); do
    if ! kill -0 "$API_PID" 2>/dev/null; then
      log "control API exited during startup"
      return 1
    fi
    if python - "$API_PORT" <<'PY'
import sys
import urllib.request
port = sys.argv[1]
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
        raise SystemExit(0 if response.status == 200 else 1)
except Exception:
    raise SystemExit(1)
PY
    then
      log "control API ready"
      return 0
    fi
    sleep 0.1
  done
  log "control API failed to become healthy"
  return 1
}

start_xvfb() {
  log "starting isolated Xvfb on ${DISPLAY}"
  Xvfb "$DISPLAY" -screen 0 1024x720x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
  XVFB_PID=$!
  for _ in $(seq 1 80); do
    if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.1
  done
  log "Xvfb failed to become ready"
  tail -n 30 /tmp/xvfb.log 2>/dev/null || true
  return 1
}

start_vnc() {
  log "starting loopback-only VNC"
  x11vnc -display "$DISPLAY" -forever -shared -passwd "$VNC_PASSWORD" -rfbport 5900 -localhost >/tmp/x11vnc.log 2>&1 &
  VNC_PID=$!
}

start_novnc() {
  log "starting loopback-only noVNC websocket proxy"
  websockify --web=/usr/share/novnc 127.0.0.1:6080 localhost:5900 >/tmp/novnc.log 2>&1 &
  NOVNC_PID=$!
}

start_chromium() {
  rm -f "$CHROME_PROFILE_DIR/SingletonLock" \
        "$CHROME_PROFILE_DIR/SingletonSocket" \
        "$CHROME_PROFILE_DIR/SingletonCookie" 2>/dev/null || true

  log "starting isolated Chromium at ${START_URL}"
  chromium \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-background-networking \
    --disable-component-update \
    --disable-client-side-phishing-detection \
    --disable-default-apps \
    --disable-extensions \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-sync \
    --disable-translate \
    --disable-breakpad \
    --disable-crash-reporter \
    --disable-notifications \
    --disable-site-isolation-trials \
    --disable-features=IsolateOrigins,site-per-process,OptimizationHints,MediaRouter,Translate,BackForwardCache,InterestFeedContentSuggestions \
    --disk-cache-size=16777216 \
    --media-cache-size=1048576 \
    --js-flags=--max-old-space-size=128 \
    --mute-audio \
    --no-first-run \
    --no-service-autorun \
    --password-store=basic \
    --renderer-process-limit=1 \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$CDP_PORT" \
    --remote-allow-origins='*' \
    --window-size=1024,720 \
    --force-device-scale-factor=1 \
    --user-data-dir="$CHROME_PROFILE_DIR" \
    "$START_URL" >/tmp/chromium.log 2>&1 &
  CHROME_PID=$!
}

local_ready() {
  python - "$API_PORT" <<'PY'
import sys
import urllib.request
port = sys.argv[1]
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/ready", timeout=4) as response:
        raise SystemExit(0 if response.status == 200 else 1)
except Exception:
    raise SystemExit(1)
PY
}

# memory.current includes reclaimable page cache. That made the safety gate
# report ~520 MiB while Render's actual process memory was ~240 MiB. Gate on
# anonymous cgroup memory instead, which is the pressure the probe can amplify.
memory_current_bytes() {
  if [[ -r /sys/fs/cgroup/memory.stat ]]; then
    awk '$1 == "anon" { print $2; found=1; exit } END { if (!found) print 0 }' /sys/fs/cgroup/memory.stat
  elif [[ -r /sys/fs/cgroup/memory.current ]]; then
    cat /sys/fs/cgroup/memory.current
  else
    printf '0\n'
  fi
}

restart_display_stack() {
  log "display stack failed; rebuilding isolated browser stack"
  stop_pid "$CHROME_PID"
  stop_pid "$NOVNC_PID"
  stop_pid "$VNC_PID"
  stop_pid "$XVFB_PID"
  start_xvfb
  start_vnc
  start_novnc
  start_chromium
}

start_api
wait_api_health
start_xvfb
start_vnc
start_novnc
if [[ "${GITLAB_STATE_ENABLED:-0}" == "1" ]]; then
  python /opt/anthares-brouser/profile_store.py restore || { log "encrypted snapshot restore failed; refusing to start"; exit 1; }
fi
start_chromium

LAST_SNAPSHOT=$(date +%s)
SNAPSHOT_INTERVAL=${GITLAB_SNAPSHOT_INTERVAL:-1800}
if [[ "${GITLAB_STATE_ENABLED:-0}" == "1" && ! -f /run/anthares-brouser/first-checkpoint-done ]]; then
  SNAPSHOT_INTERVAL=${GITLAB_FIRST_SNAPSHOT_INTERVAL:-120}
fi
READY_FAILURES=0
MAX_READY_FAILURES=${MAX_READY_FAILURES:-6}
SUPERVISOR_INTERVAL=${SUPERVISOR_INTERVAL:-5}
KWAI_PROBE_DONE=0
KWAI_PROBE_ATTEMPTS=0
KWAI_PROBE_MAX_ATTEMPTS=${KWAI_PROBE_MAX_ATTEMPTS:-1}
KWAI_PROBE_TIMEOUT=${KWAI_PROBE_TIMEOUT:-45}
KWAI_PROBE_MEMORY_MAX_BYTES=${KWAI_PROBE_MEMORY_MAX_BYTES:-300000000}

log "supervisor active"
while kill -0 "$API_PID" 2>/dev/null; do
  sleep "$SUPERVISOR_INTERVAL"

  if ! kill -0 "$XVFB_PID" 2>/dev/null; then
    restart_display_stack
    READY_FAILURES=0
    continue
  fi

  if ! kill -0 "$VNC_PID" 2>/dev/null; then
    log "VNC exited; restarting"
    start_vnc
  fi

  if ! kill -0 "$NOVNC_PID" 2>/dev/null; then
    log "noVNC proxy exited; restarting"
    start_novnc
  fi

  if ! kill -0 "$CHROME_PID" 2>/dev/null; then
    log "Chromium exited; restarting with the same persistent profile"
    tail -n 20 /tmp/chromium.log 2>/dev/null || true
    start_chromium
    READY_FAILURES=0
    continue
  fi

  if [[ "${GITLAB_STATE_ENABLED:-0}" == "1" ]] && (( $(date +%s) - LAST_SNAPSHOT >= SNAPSHOT_INTERVAL )); then
    log "checkpointing encrypted browser profile"
    stop_pid "$CHROME_PID"
    if python /opt/anthares-brouser/profile_store.py backup; then
      log "encrypted profile checkpoint committed"
      touch /run/anthares-brouser/first-checkpoint-done
      SNAPSHOT_INTERVAL=${GITLAB_SNAPSHOT_INTERVAL:-1800}
    else
      log "encrypted profile checkpoint failed"
    fi
    start_chromium
    LAST_SNAPSHOT=$(date +%s)
    READY_FAILURES=0
    continue
  fi

  if local_ready; then
    if (( READY_FAILURES > 0 )); then
      log "browser readiness recovered"
    fi
    READY_FAILURES=0
    if (( KWAI_PROBE_DONE == 0 && KWAI_PROBE_ATTEMPTS < KWAI_PROBE_MAX_ATTEMPTS )); then
      CURRENT_MEMORY=$(memory_current_bytes)
      if (( CURRENT_MEMORY > 0 && CURRENT_MEMORY >= KWAI_PROBE_MEMORY_MAX_BYTES )); then
        log "deferring Kwai runtime probe; anon_memory=${CURRENT_MEMORY} limit=${KWAI_PROBE_MEMORY_MAX_BYTES}"
      else
        KWAI_PROBE_ATTEMPTS=$((KWAI_PROBE_ATTEMPTS + 1))
        log "running bounded fail-closed Kwai runtime probe (${KWAI_PROBE_ATTEMPTS}/${KWAI_PROBE_MAX_ATTEMPTS})"
        set +e
        timeout "${KWAI_PROBE_TIMEOUT}s" python /opt/anthares-brouser/kwai_runtime_probe.py
        PROBE_RC=$?
        set -e
        if (( PROBE_RC == 0 )); then
          KWAI_PROBE_DONE=1
          log "Kwai identity and upload surface verified"
        elif (( PROBE_RC == 124 )); then
          log "Kwai runtime probe timed out safely"
        else
          log "Kwai runtime probe did not prove authenticated upload readiness (rc=${PROBE_RC})"
        fi
      fi
    fi
  else
    READY_FAILURES=$((READY_FAILURES + 1))
    log "readiness probe failed (${READY_FAILURES}/${MAX_READY_FAILURES})"
    if (( READY_FAILURES >= MAX_READY_FAILURES )); then
      log "CDP remained unhealthy; restarting Chromium"
      tail -n 20 /tmp/chromium.log 2>/dev/null || true
      stop_pid "$CHROME_PID"
      start_chromium
      READY_FAILURES=0
    fi
  fi
done

log "control API exited; terminating container so Render can restart it"
wait "$API_PID" || exit $?
