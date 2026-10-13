#!/usr/bin/env bash
set -euo pipefail

: "${ANTHARES_EXECUTOR_TOKEN:?ANTHARES_EXECUTOR_TOKEN is required}"
export CHROME_PROFILE_DIR=${CHROME_PROFILE_DIR:-/data/chrome-profile}
export CDP_PORT=${CDP_PORT:-9222}
PORT=${PORT:-8080}
STATE_FILE=${ANTHARES_STATE_FILE:-/run/anthares-executor/state.json}
mkdir -p "$CHROME_PROFILE_DIR" "$(dirname "$STATE_FILE")"

CHROME_PID=""
API_PID=""

log(){ printf '[anthares-executor] %s\n' "$*"; }
stop_pid(){ local p="${1:-}"; [[ -z "$p" ]] && return 0; kill -0 "$p" 2>/dev/null || return 0; kill -TERM "$p" 2>/dev/null || true; for _ in $(seq 1 40); do kill -0 "$p" 2>/dev/null || break; sleep .25; done; kill -0 "$p" 2>/dev/null && kill -KILL "$p" 2>/dev/null || true; wait "$p" 2>/dev/null || true; }

backup_state(){
  if [[ "${GITLAB_STATE_ENABLED:-0}" == "1" ]]; then
    log "checkpointing encrypted Chromium profile"
    python /opt/anthares-executor/profile_store.py backup || log "encrypted checkpoint failed"
  fi
}
cleanup(){
  trap - EXIT INT TERM
  stop_pid "$CHROME_PID"
  backup_state
  stop_pid "$API_PID"
}
trap cleanup EXIT INT TERM

if [[ "${GITLAB_STATE_ENABLED:-0}" == "1" ]]; then
  log "restoring encrypted Chromium profile"
  if RESTORE_JSON=$(python /opt/anthares-executor/profile_store.py restore); then
    printf '%s' "$RESTORE_JSON" > "$STATE_FILE"
  else
    log "state restore failed; refusing to start with an empty profile"
    exit 3
  fi
else
  printf '%s' '{"ok":true,"source":"ephemeral","restored":false}' > "$STATE_FILE"
fi

rm -f "$CHROME_PROFILE_DIR"/SingletonLock "$CHROME_PROFILE_DIR"/SingletonSocket "$CHROME_PROFILE_DIR"/SingletonCookie 2>/dev/null || true
log "starting headless Chromium"
chromium \
  --headless=new \
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
  --disable-breakpad \
  --disable-crash-reporter \
  --disable-notifications \
  --disable-site-isolation-trials \
  --disable-features=IsolateOrigins,site-per-process,OptimizationHints,MediaRouter,Translate,BackForwardCache,InterestFeedContentSuggestions \
  --disk-cache-size=8388608 \
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
  --user-data-dir="$CHROME_PROFILE_DIR" \
  about:blank >/tmp/anthares-chromium.log 2>&1 &
CHROME_PID=$!

for _ in $(seq 1 120); do
  kill -0 "$CHROME_PID" 2>/dev/null || { tail -n 30 /tmp/anthares-chromium.log >&2 || true; exit 4; }
  if python - "$CDP_PORT" <<'PY'
import sys, urllib.request
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/json/version", timeout=.8) as r:
        raise SystemExit(0 if r.status == 200 else 1)
except Exception: raise SystemExit(1)
PY
  then break; fi
  sleep .25
done

log "starting authenticated control API"
uvicorn app:app --app-dir /opt/anthares-executor --host 0.0.0.0 --port "$PORT" --no-access-log &
API_PID=$!
wait -n "$CHROME_PID" "$API_PID"
log "runtime process exited"
exit 5
