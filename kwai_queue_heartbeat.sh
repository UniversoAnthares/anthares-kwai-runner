#!/usr/bin/env bash
set -Eeuo pipefail

INTERVAL="${KWAI_LEASE_RENEW_INTERVAL_SECONDS:-120}"
TTL="${KWAI_LEASE_RENEW_TTL_SECONDS:-600}"
: "${KWAI_QUEUE_JOB_ID:?KWAI_QUEUE_JOB_ID is required}"
: "${KWAI_LEASE_GENERATION:?KWAI_LEASE_GENERATION is required}"
[[ "$INTERVAL" =~ ^[0-9]+$ ]] && [ "$INTERVAL" -ge 15 ] || { echo "INVALID_RENEW_INTERVAL"; exit 46; }
[[ "$TTL" =~ ^[0-9]+$ ]] && [ "$TTL" -gt "$INTERVAL" ] || { echo "INVALID_RENEW_TTL"; exit 47; }
[ "$#" -gt 0 ] || { echo "usage: kwai_queue_heartbeat.sh command [args...]"; exit 48; }

# Fence the publication immediately. Do not wait one heartbeat interval before
# proving that this holder still owns the current lease generation.
if ! bash kwai_queue_state.sh renew "$TTL"; then
  echo "STATE=FAILED_SAFE REASON=initial-lease-renew-failed"
  exit 49
fi

tmp="$(mktemp)"
cleanup(){ rm -f "$tmp"; }
trap cleanup EXIT

heartbeat(){
  while kill -0 "$1" 2>/dev/null; do
    sleep "$INTERVAL" &
    wait $! || true
    kill -0 "$1" 2>/dev/null || return 0
    if ! bash kwai_queue_state.sh renew "$TTL" >>"$tmp" 2>&1; then
      echo "LEASE_HEARTBEAT_FAILED" >&2
      cat "$tmp" >&2 || true
      kill -TERM "$1" 2>/dev/null || true
      return 49
    fi
    : >"$tmp"
  done
}

"$@" &
child=$!
heartbeat "$child" &
hb=$!

set +e
wait "$child"
rc=$?
child_done=1
if kill -0 "$hb" 2>/dev/null; then
  kill -TERM "$hb" 2>/dev/null || true
  wait "$hb" 2>/dev/null || true
  hrc=0
else
  wait "$hb" 2>/dev/null
  hrc=$?
fi
set -e

if [ "$hrc" -ne 0 ]; then
  echo "STATE=FAILED_SAFE REASON=lease-heartbeat-lost"
  exit "$hrc"
fi
exit "$rc"
