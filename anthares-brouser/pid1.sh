#!/usr/bin/env bash
set -euo pipefail

child=""

terminate() {
  trap - TERM INT EXIT
  if [[ -n "${child}" ]] && kill -0 "$child" 2>/dev/null; then
    kill -TERM "$child" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$child" 2>/dev/null || break
      sleep 1
    done
    if kill -0 "$child" 2>/dev/null; then
      echo '[anthares-browser] graceful shutdown exceeded 20s; forcing container child exit'
      kill -KILL "$child" 2>/dev/null || true
    fi
    wait "$child" 2>/dev/null || true
  fi
  exit 0
}

trap terminate TERM INT
/opt/anthares-brouser/start.sh &
child=$!
wait "$child"
status=$?
child=""
exit "$status"
