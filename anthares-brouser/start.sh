#!/usr/bin/env bash
set -euo pipefail

: "${VNC_PASSWORD:?VNC_PASSWORD is required}"
: "${CONTROL_TOKEN:?CONTROL_TOKEN is required}"

export DISPLAY=${DISPLAY:-:99}
export CHROME_PROFILE_DIR=${CHROME_PROFILE_DIR:-/data/chrome-profile}
START_URL=${START_URL:-https://www.kwai.com/}
CDP_PORT=${CDP_PORT:-9222}
# The CDP websocket is strictly loopback-only. Explicitly bypass any proxy
# configuration inherited/injected into the container; websocket-client can
# otherwise tunnel ws://localhost through an HTTP proxy and the control API
# reports that as a generic 503 even while /json/list is healthy.
export NO_PROXY="127.0.0.1,localhost,::1${NO_PROXY:+,$NO_PROXY}"
export no_proxy="127.0.0.1,localhost,::1${no_proxy:+,$no_proxy}"
mkdir -p "$CHROME_PROFILE_DIR" /run/anthares-brouser

Xvfb "$DISPLAY" -screen 0 1440x900x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
XVFB_PID=$!

for _ in $(seq 1 50); do
  xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 && break
  sleep 0.1
done

x11vnc -display "$DISPLAY" -forever -shared -passwd "$VNC_PASSWORD" -rfbport 5900 -localhost >/tmp/x11vnc.log 2>&1 &
VNC_PID=$!

# noVNC must never listen on a public interface without an authenticated
# reverse proxy. Bind loopback; expose only through an authenticated tunnel.
websockify --web=/usr/share/novnc 127.0.0.1:6080 localhost:5900 >/tmp/novnc.log 2>&1 &
NOVNC_PID=$!

chromium \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-background-networking \
  --disable-component-update \
  --no-first-run \
  --start-maximized \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port="$CDP_PORT" \
  --remote-allow-origins='*' \
  --user-data-dir="$CHROME_PROFILE_DIR" \
  "$START_URL" >/tmp/chromium.log 2>&1 &
CHROME_PID=$!

uvicorn app:app --host 0.0.0.0 --port 8080 --app-dir /opt/anthares-brouser >/tmp/api.log 2>&1 &
API_PID=$!

cleanup() {
  kill "$API_PID" "$CHROME_PID" "$NOVNC_PID" "$VNC_PID" "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait -n "$API_PID" "$CHROME_PID" "$NOVNC_PID" "$VNC_PID" "$XVFB_PID"
