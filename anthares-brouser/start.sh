#!/usr/bin/env bash
set -euo pipefail

: "${VNC_PASSWORD:?VNC_PASSWORD is required}"
: "${CONTROL_TOKEN:?CONTROL_TOKEN is required}"

export DISPLAY=${DISPLAY:-:99}
export CHROME_PROFILE_DIR=${CHROME_PROFILE_DIR:-/data/chrome-profile}
START_URL=${START_URL:-https://www.kwai.com/}
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
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  stop_pid "$CHROME_PID"
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
  Xvfb "$DISPLAY" -screen 0 1440x900x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
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
  x11vnc -display "$DISPLAY" -forever -shared -nopw -rfbport 5900 -localhost >/tmp/x11vnc.log 2>&1 &
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
    --disable-sync \
    --disable-translate \
    --no-first-run \
    --no-service-autorun \
    --password-store=basic \
    --renderer-process-limit=3 \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$CDP_PORT" \
    --remote-allow-origins='*' \
    --start-maximized \
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
start_chromium

# End-to-end check: signed cookie -> FastAPI WebSocket -> loopback x11vnc RFB.
(
  for attempt in $(seq 1 20); do
    if python - "$API_PORT" <<'PY'
import sys
import websocket
sys.path.insert(0, "/opt/anthares-brouser")
from novnc_gateway import COOKIE_NAME, _issue
port = sys.argv[1]
ws = websocket.create_connection(
    f"ws://127.0.0.1:{port}/novnc/websockify",
    origin="https://anthares-browser-qa-render.onrender.com",
    cookie=f"{COOKIE_NAME}={_issue()}",
    timeout=5,
)
try:
    banner = ws.recv()
    assert isinstance(banner, bytes) and banner.startswith(b"RFB "), repr(banner)[:80]
finally:
    ws.close()
PY
    then
      log "authenticated noVNC websocket-to-RFB handshake PASS"
      exit 0
    fi
    sleep 2
  done
  log "authenticated noVNC websocket-to-RFB handshake FAILED"
) &

READY_FAILURES=0
MAX_READY_FAILURES=${MAX_READY_FAILURES:-6}
SUPERVISOR_INTERVAL=${SUPERVISOR_INTERVAL:-5}

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

  if local_ready; then
    if (( READY_FAILURES > 0 )); then
      log "browser readiness recovered"
    fi
    READY_FAILURES=0
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
