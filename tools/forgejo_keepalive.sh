#!/usr/bin/env bash
set -euo pipefail

# Single-owner recovery of the existing Hostinger Forgejo instance.
# This file never changes Git refs, service configuration or credentials.
base="$HOME/.anthares-forgejo"
sock="$base/forgejo.sock"
bin="$base/bin/forgejo"
conf="$base/custom/conf/app.ini"
log="$base/forgejo.log"
status_file="$base/keepalive-last.json"

# One small atomic record per scheduled tick; requires no shell spawn for a date.
# Monitoring must never block health recovery when the hosting process cap is tight.
record_status() {
  local state="$1" tmp="$base/.keepalive-last.$"
  if printf '{"checked_epoch":%s,"state":"%s"}\n' "${EPOCHSECONDS:-0}" "$state" > "$tmp" 2>/dev/null; then
    mv -f -- "$tmp" "$status_file" 2>/dev/null || :
  fi
  return 0
}

if [[ ! -d "$base" || ! -x "$bin" || ! -f "$conf" ]]; then
  record_status INSTALLATION_MISSING
  echo "FORGEJO_KEEPALIVE_INSTALLATION_MISSING" >&2
  exit 78
fi

healthy() {
  curl -fsS --connect-timeout 2 --max-time 3 --unix-socket "$sock" \
    http://unix/api/v1/version >/dev/null 2>&1
}

# The existing daemon may have inherited fd9 from an older keepalive release.
# A healthy daemon must be acknowledged even when that historic lock is held.
if healthy; then
  record_status HEALTHY
  echo "FORGEJO_KEEPALIVE_ALREADY_HEALTHY=PASS"
  exit 0
fi

# Only an unhealthy daemon requires exclusive recovery ownership.
exec 9>>"$base/keepalive.lock"
if ! flock -n 9; then
  if healthy; then
    record_status HEALTHY
  echo "FORGEJO_KEEPALIVE_ALREADY_HEALTHY=PASS"
    exit 0
  fi
  record_status RECOVERY_BUSY
  echo "FORGEJO_KEEPALIVE_RECOVERY_BUSY" >&2
  exit 75
fi

# Avoid destroying a live socket after one transient HTTP/Unix connection error.
for attempt in 1 2 3; do
  if healthy; then
    record_status HEALTHY
  echo "FORGEJO_KEEPALIVE_ALREADY_HEALTHY=PASS"
    exit 0
  fi
  if [[ "$attempt" -lt 3 ]]; then sleep 1; fi
done

# Fail closed when the original daemon still runs and needs an operator diagnosis.
# Match the existing Forgejo web binary even with alternate config argv; never kill it.
if [[ ! -d /proc || ! -r /proc/self/cmdline ]]; then
  record_status PROCESS_INSPECTION_UNAVAILABLE
  echo "FORGEJO_KEEPALIVE_PROCESS_INSPECTION_UNAVAILABLE" >&2
  exit 70
fi
for cmdline in /proc/[0-9]*/cmdline; do
  [[ -r "$cmdline" ]] || continue
  argv=()
  if ! mapfile -d "" -t argv < "$cmdline" 2>/dev/null; then continue; fi
  if [[ "${argv[0]-}" == "$bin" && "${argv[1]-}" == "web" ]]; then
    record_status RUNNING_BUT_UNHEALTHY
    echo "FORGEJO_KEEPALIVE_RUNNING_BUT_UNHEALTHY" >&2
    exit 70
  fi
done

# Never unlink a symlink, ordinary file, or another unexpected occupant.
if [[ -L "$sock" ]]; then
  record_status UNEXPECTED_SOCKET_SYMLINK
  echo "FORGEJO_KEEPALIVE_UNEXPECTED_SOCKET_SYMLINK" >&2
  exit 73
fi
if [[ -e "$sock" && ! -S "$sock" ]]; then
  record_status UNEXPECTED_SOCKET_TYPE
  echo "FORGEJO_KEEPALIVE_UNEXPECTED_SOCKET_TYPE" >&2
  exit 73
fi
if [[ -S "$sock" ]]; then rm -- "$sock"; fi

GOMAXPROCS=2 nohup "$bin" web --config "$conf" 9>&- >>"$log" 2>&1 </dev/null &
new_pid=$!
for attempt in $(seq 1 20); do
  if healthy; then
    record_status RECOVERED
    echo "FORGEJO_KEEPALIVE_RECOVERED=PASS pid=$new_pid"
    exit 0
  fi
  if ! kill -0 "$new_pid" 2>/dev/null; then
    record_status DAEMON_EXITED
    echo "FORGEJO_KEEPALIVE_DAEMON_EXITED" >&2
    exit 1
  fi
  sleep 1
done
record_status START_TIMEOUT
echo "FORGEJO_KEEPALIVE_START_TIMEOUT" >&2
exit 1
