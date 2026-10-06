#!/usr/bin/env bash
set -Eeuo pipefail

ACCOUNT_ID="${KWAI_ACCOUNT_ID:-primary}"
case "$ACCOUNT_ID" in primary|secondary) ;; *) echo "invalid KWAI_ACCOUNT_ID" >&2; exit 2 ;; esac
STATE_FILE="${KWAI_SESSION_FILE:-kwai-session-${ACCOUNT_ID}.enc}"
PKG="com.kwai.video"

log(){ printf '%s\n' "$*"; }

root_ready(){
  adb root >/dev/null 2>&1 || true
  adb wait-for-device
  adb shell id 2>/dev/null | grep -q 'uid=0'
}

restore_state(){
  [ -s "$STATE_FILE" ] || { log "KWAI_SESSION_CACHE_MISS"; return 1; }
  [ -n "${KWAI_PASSWORD:-}" ] || { log "KWAI_SESSION_KEY_MISSING"; return 1; }
  root_ready || { log "KWAI_SESSION_ROOT_UNAVAILABLE"; return 1; }
  adb shell am force-stop "$PKG" >/dev/null 2>&1 || true
  if openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:KWAI_PASSWORD -in "$STATE_FILE" 2>/dev/null |
      adb shell 'tar -C /data/user/0 -xpf -' >/dev/null 2>&1; then
    adb shell "restorecon -RF /data/user/0/$PKG" >/dev/null 2>&1 || true
    log "KWAI_SESSION_RESTORED"
    return 0
  fi
  log "KWAI_SESSION_RESTORE_FAILED"
  return 1
}

save_state(){
  [ -n "${KWAI_PASSWORD:-}" ] || { log "KWAI_SESSION_KEY_MISSING"; return 1; }
  root_ready || { log "KWAI_SESSION_ROOT_UNAVAILABLE"; return 1; }
  tmp="${STATE_FILE}.tmp"
  rm -f "$tmp"
  if adb exec-out "tar -C /data/user/0 -cpf - $PKG" 2>/dev/null |
      openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -pass env:KWAI_PASSWORD -out "$tmp"; then
    test -s "$tmp" || return 1
    mv "$tmp" "$STATE_FILE"
    chmod 600 "$STATE_FILE"
    log "KWAI_SESSION_SAVED_ENCRYPTED"
    return 0
  fi
  rm -f "$tmp"
  log "KWAI_SESSION_SAVE_FAILED"
  return 1
}

case "${1:-}" in
  restore) restore_state ;;
  save) save_state ;;
  *) echo "usage: $0 {restore|save}" >&2; exit 2 ;;
esac
