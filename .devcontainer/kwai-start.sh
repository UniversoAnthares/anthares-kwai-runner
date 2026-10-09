#!/usr/bin/env bash
set -euo pipefail

# Codespaces-only, private-port desktop. Never launch an Android emulator.
PRIVATE_HOME="${HOME}/.kwai-remote-private"
LOGS="${PRIVATE_HOME}/logs"
install -d -m 700 "${PRIVATE_HOME}" "${LOGS}" "${PRIVATE_HOME}/chrome-profile"
chmod 700 "${PRIVATE_HOME}" "${PRIVATE_HOME}/chrome-profile"
export DISPLAY=:99

start_once() {
  local name="$1"
  shift
  local pidfile="${PRIVATE_HOME}/${name}.pid"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "KWAI_CODESPACE_${name}=already_running"
    return
  fi
  nohup "$@" >"${LOGS}/${name}.log" 2>&1 </dev/null &
  echo "$!" >"$pidfile"
  echo "KWAI_CODESPACE_${name}=started"
}

restart_current_bridge() {
  local pidfile="${PRIVATE_HOME}/bridge.pid"
  local pids=()
  local pid cmd

  # The bridge is stateless apart from its local seen-comment ledger. Restarting
  # it must never restart Chrome or touch the persistent browser profile.
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
      pids+=("$pid")
    fi
  fi
  while IFS= read -r pid; do
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    [[ " ${pids[*]-} " == *" $pid "* ]] || pids+=("$pid")
  done < <(pgrep -f 'python.*\.devcontainer/kwai-command-bridge\.py' || true)

  for pid in "${pids[@]-}"; do
    [[ -n "$pid" ]] || continue
    cmd="$(tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true)"
    if [[ "$cmd" != *".devcontainer/kwai-command-bridge.py"* ]]; then
      echo "KWAI_CODESPACE_bridge=pid_mismatch_refusing_to_kill" >&2
      return 1
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
  start_once bridge "${PRIVATE_HOME}/venv/bin/python" -u .devcontainer/kwai-command-bridge.py
  echo "KWAI_CODESPACE_bridge=current_checkout_loaded;chrome_profile_untouched=true"
}

start_once xvfb Xvfb :99 -screen 0 1440x900x24 -nolisten tcp
sleep 2
start_once openbox openbox-session

# VNC and Chrome DevTools listen on loopback only; do NOT make forwarded ports public.
start_once vnc x11vnc -display :99 -localhost -rfbport 5900 -nopw -forever -shared -quiet
start_once novnc websockify --web=/usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900

start_once chrome chromium \
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

start_once inspector "${PRIVATE_HOME}/venv/bin/python" -u .devcontainer/kwai-identity-guard.py
restart_current_bridge

echo "KWAI_CODESPACE_PRIVATE_NOVNC=http://127.0.0.1:6080/vnc.html"
echo "KWAI_CODESPACE_PRIVATE_IDENTITY=http://127.0.0.1:8765/"
echo "KWAI_CODESPACE_REQUIRED_PORT_VISIBILITY=private_check_in_GitHub_PORTS"
echo "KWAI_CODESPACE_PROFILE_WARNING=contains_sensitive_browser_state;never_commit_or_publish"
