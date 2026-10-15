#!/usr/bin/env bash
set -euo pipefail

PERSISTENT_ROOT="${ANTHARES_PERSISTENT_ROOT:-/workspaces/.anthares-private}"
PRIVATE_HOME="${TIKTOK_PRIVATE_HOME:-${PERSISTENT_ROOT}/tiktok}"
LOGS="${PRIVATE_HOME}/logs"
PROFILE="${PRIVATE_HOME}/chrome-profile"
install -d -m 700 "${PERSISTENT_ROOT}" "${PRIVATE_HOME}" "${LOGS}" "${PROFILE}"
chmod 700 "${PERSISTENT_ROOT}" "${PRIVATE_HOME}" "${PROFILE}"
export DISPLAY=:99

pid_matches() {
  local pid="$1" marker="$2" cmd
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  cmd="$(tr '\0' ' ' <"/proc/${pid}/cmdline" 2>/dev/null || true)"
  [[ -n "$cmd" && "$cmd" == *"$marker"* ]]
}

start_once() {
  local name="$1" marker="$2"; shift 2
  local pidfile="${PRIVATE_HOME}/${name}.pid" pid
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  if pid_matches "$pid" "$marker"; then
    echo "TIKTOK_CODESPACE_${name}=already_running"
    return
  fi
  rm -f "$pidfile"
  nohup "$@" >"${LOGS}/${name}.log" 2>&1 </dev/null &
  echo "$!" >"$pidfile"
  echo "TIKTOK_CODESPACE_${name}=started"
}

# Reuse Kwai's private Xvfb/noVNC desktop. Only the TikTok Chrome profile and
# local CDP endpoint are separate. Nothing is exported to the repository.
start_once chrome chromium chromium \
  --no-sandbox \
  --disable-dev-shm-usage \
  --no-first-run \
  --no-default-browser-check \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9223 \
  --user-data-dir="${PROFILE}" \
  --window-size=1400,860 \
  https://www.tiktok.com/login

start_once inspector tiktok-auth-guard.py "${PRIVATE_HOME}/venv/bin/python" -u .devcontainer/tiktok-auth-guard.py

echo "TIKTOK_CODESPACE_PRIVATE_NOVNC=http://127.0.0.1:6080/vnc.html"
echo "TIKTOK_CODESPACE_PRIVATE_IDENTITY=http://127.0.0.1:8766/"
echo "TIKTOK_CODESPACE_REQUIRED_PORT_VISIBILITY=private_check_in_GitHub_PORTS"
echo "TIKTOK_CODESPACE_PROFILE_STORAGE=${PROFILE}"
echo "TIKTOK_CODESPACE_PROFILE_WARNING=contains_sensitive_browser_state;never_commit_or_publish"
