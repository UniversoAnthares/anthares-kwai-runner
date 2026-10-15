#!/usr/bin/env bash
set -euo pipefail

# Codespaces-only, private-port desktop. Never launch an Android emulator.
PERSISTENT_ROOT="${ANTHARES_PERSISTENT_ROOT:-/workspaces/.anthares-private}"
PRIVATE_HOME="${KWAI_PRIVATE_HOME:-${PERSISTENT_ROOT}/kwai}"
LOGS="${PRIVATE_HOME}/logs"
install -d -m 700 "${PERSISTENT_ROOT}" "${PRIVATE_HOME}" "${LOGS}" "${PRIVATE_HOME}/chrome-profile"
chmod 700 "${PERSISTENT_ROOT}" "${PRIVATE_HOME}" "${PRIVATE_HOME}/chrome-profile"
export DISPLAY=:99

service_marker() {
  case "$1" in
    xvfb) echo 'Xvfb' ;;
    openbox) echo 'openbox' ;;
    vnc) echo 'x11vnc' ;;
    novnc) echo 'websockify' ;;
    chrome) echo 'chromium' ;;
    inspector) echo 'kwai-identity-guard.py' ;;
    bridge) echo 'kwai-command-bridge-v2.py' ;;
    *) return 1 ;;
  esac
}

pid_matches_service() {
  local name="$1" pid="$2" marker cmd
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  marker="$(service_marker "$name")" || return 1
  cmd="$(tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true)"
  [[ -n "$cmd" && "$cmd" == *"$marker"* ]]
}

start_once() {
  local name="$1"
  shift
  local pidfile="${PRIVATE_HOME}/${name}.pid" pid
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  if pid_matches_service "$name" "$pid"; then
    echo "KWAI_CODESPACE_${name}=already_running"
    return
  fi
  if [[ -n "$pid" ]]; then
    echo "KWAI_CODESPACE_${name}=stale_pidfile_ignored"
    rm -f "$pidfile"
  fi
  nohup "$@" >"${LOGS}/${name}.log" 2>&1 </dev/null &
  echo "$!" >"$pidfile"
  echo "KWAI_CODESPACE_${name}=started"
}

kill_service() {
  local name="$1" pidfile="${PRIVATE_HOME}/${name}.pid" pid cmd marker
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  marker="$(service_marker "$name")" || return 0
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    cmd="$(tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true)"
    if [[ "$cmd" == *"$marker"* ]]; then
      kill "$pid" 2>/dev/null || true
      for _ in 1 2 3 4 5 6 7 8 9 10; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.2
      done
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$pidfile"
}

port_open() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket,sys
s=socket.socket(); s.settimeout(1)
try:
    s.connect(('127.0.0.1',int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
PY
}

display_ready() {
  [[ -S /tmp/.X11-unix/X99 ]] && xdpyinfo -display :99 >/dev/null 2>&1
}

vnc_ready() {
  local pid
  pid="$(cat "${PRIVATE_HOME}/vnc.pid" 2>/dev/null || true)"
  pid_matches_service vnc "$pid" && port_open 5900
}

novnc_ready() {
  local pid
  pid="$(cat "${PRIVATE_HOME}/novnc.pid" 2>/dev/null || true)"
  pid_matches_service novnc "$pid" && port_open 6080 && curl --noproxy '*' -fsS --max-time 3 http://127.0.0.1:6080/vnc.html -o /dev/null
}

recover_desktop_stack() {
  if ! display_ready; then
    kill_service openbox
    kill_service vnc
    kill_service novnc
    kill_service xvfb
    rm -f /tmp/.X99-lock
    start_once xvfb Xvfb :99 -screen 0 1440x900x24 -nolisten tcp
    for _ in $(seq 1 30); do display_ready && break; sleep 0.2; done
    display_ready || { echo "KWAI_CODESPACE_XVFB=unhealthy" >&2; return 1; }
  fi

  start_once openbox openbox-session

  if ! vnc_ready; then
    kill_service vnc
    start_once vnc x11vnc -display :99 -localhost -rfbport 5900 -nopw -forever -shared -quiet
    for _ in $(seq 1 30); do vnc_ready && break; sleep 0.2; done
    vnc_ready || { echo "KWAI_CODESPACE_VNC=unhealthy" >&2; return 1; }
  fi

  if ! novnc_ready; then
    kill_service novnc
    start_once novnc websockify --web=/usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900
    for _ in $(seq 1 30); do novnc_ready && break; sleep 0.2; done
    novnc_ready || { echo "KWAI_CODESPACE_NOVNC=unhealthy" >&2; return 1; }
  fi

  echo "KWAI_CODESPACE_DESKTOP_STACK=healthy"
}

restart_current_bridge() {
  local pidfile="${PRIVATE_HOME}/bridge.pid"
  local pids=()
  local pid cmd
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if pid_matches_service bridge "$pid"; then
      pids+=("$pid")
    elif [[ -n "$pid" ]]; then
      echo "KWAI_CODESPACE_bridge=stale_pidfile_ignored"
      rm -f "$pidfile"
    fi
  fi
  while IFS= read -r pid; do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    [[ " ${pids[*]-} " == *" $pid "* ]] || pids+=("$pid")
  done < <(pgrep -f 'python.*\.devcontainer/kwai-command-bridge(-v2)?\.py' || true)
  for pid in "${pids[@]-}"; do
    [[ -n "$pid" ]] || continue
    cmd="$(tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true)"
    if [[ "$cmd" != *".devcontainer/kwai-command-bridge.py"* && "$cmd" != *".devcontainer/kwai-command-bridge-v2.py"* ]]; then
      echo "KWAI_CODESPACE_bridge=unrelated_pid_ignored"
      continue
    fi
    kill "$pid"
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.2
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "KWAI_CODESPACE_bridge=old_process_did_not_exit" >&2
      return 1
    fi
  done
  rm -f "$pidfile"
  start_once bridge "${PRIVATE_HOME}/venv/bin/python" -u .devcontainer/kwai-command-bridge-v2.py
  echo "KWAI_CODESPACE_bridge=v2_latest_comments_loaded;chrome_profile_untouched=true"
}

recover_desktop_stack
if [[ ! -f "${PRIVATE_HOME}/desktop-watchdog.pid" ]] || ! kill -0 "$(cat "${PRIVATE_HOME}/desktop-watchdog.pid")" 2>/dev/null; then
  (
    while true; do
      sleep 10
      recover_desktop_stack || true
    done
  ) >"${LOGS}/desktop-watchdog.log" 2>&1 </dev/null &
  echo "$!" >"${PRIVATE_HOME}/desktop-watchdog.pid"
fi

start_once chrome chromium chromium \
  --no-sandbox \
  --disable-dev-shm-usage \
  --no-first-run \
  --no-default-browser-check \
  --disable-background-networking \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir="${PRIVATE_HOME}/chrome-profile" \
  --window-size=1400,860 \
  https://www.kwai.com/

start_once inspector kwai-identity-guard.py "${PRIVATE_HOME}/venv/bin/python" -u .devcontainer/kwai-identity-guard.py
restart_current_bridge

# Keep the TikTok authentication path attached to the same private desktop and
# refresh lifecycle, while preserving an entirely separate browser profile.
if [[ -f .devcontainer/tiktok-start.sh ]]; then
  bash .devcontainer/tiktok-start.sh
fi

echo "KWAI_CODESPACE_PRIVATE_NOVNC=http://127.0.0.1:6080/vnc.html"
echo "KWAI_CODESPACE_PRIVATE_IDENTITY=http://127.0.0.1:8765/"
echo "KWAI_CODESPACE_REQUIRED_PORT_VISIBILITY=private_check_in_GitHub_PORTS"
echo "KWAI_CODESPACE_PROFILE_STORAGE=${PRIVATE_HOME}/chrome-profile"
echo "KWAI_CODESPACE_PROFILE_WARNING=contains_sensitive_browser_state;never_commit_or_publish"
