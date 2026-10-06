#!/usr/bin/env bash
set -euo pipefail
base="$HOME/.anthares-forgejo"
sock="$base/forgejo.sock"
bin="$base/bin/forgejo"
conf="$base/custom/conf/app.ini"
log="$base/forgejo.log"
exec 9>"$base/keepalive.lock"
flock -n 9 || exit 0
if ! curl -fsS --unix-socket "$sock" http://unix/api/v1/version >/dev/null 2>&1; then
  rm -f "$sock"
  nohup "$bin" web --config "$conf" >>"$log" 2>&1 </dev/null &
  for i in $(seq 1 20); do curl -fsS --unix-socket "$sock" http://unix/api/v1/version >/dev/null 2>&1 && exit 0; sleep 1; done
  exit 1
fi
