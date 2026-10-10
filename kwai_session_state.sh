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

# Never decrypt directly into the live application directory: a wrong key or
# truncated archive can otherwise leave an unusable partially restored profile.
restore_state(){
  [ -s "$STATE_FILE" ] || { log "KWAI_SESSION_CACHE_MISS"; return 1; }
  [ -n "${KWAI_PASSWORD:-}" ] || { log "KWAI_SESSION_KEY_MISSING"; return 1; }
  root_ready || { log "KWAI_SESSION_ROOT_UNAVAILABLE"; return 1; }
  local archive staging
  archive="$(mktemp)"
  staging="/data/local/tmp/kwai-restore-$$"
  trap 'rm -f "$archive"; adb shell rm -rf "$staging" >/dev/null 2>&1 || true' RETURN
  if ! openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:KWAI_PASSWORD -in "$STATE_FILE" -out "$archive" 2>/dev/null; then
    log "KWAI_SESSION_DECRYPT_FAILED"; return 1
  fi
  if ! tar -tf "$archive" 2>/dev/null | python3 -c '
import sys
from pathlib import PurePosixPath
paths=[line.strip() for line in sys.stdin if line.strip()]
if not paths: sys.exit(1)
for name in paths:
 p=PurePosixPath(name)
 if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0]!="com.kwai.video": sys.exit(2)
'; then
    log "KWAI_SESSION_ARCHIVE_INVALID"; return 1
  fi
  adb shell mkdir -p "$staging"
  if ! adb push "$archive" "$staging/session.tar" >/dev/null 2>&1; then
    log "KWAI_SESSION_TRANSFER_FAILED"; return 1
  fi
  # Extract to a sandbox first. The app is stopped only after the archive
  # has passed integrity and path checks.
  if ! adb shell "mkdir -p '$staging/unpacked' && tar -C '$staging/unpacked' -xpf '$staging/session.tar' && test -d '$staging/unpacked/$PKG'" >/dev/null 2>&1; then
    log "KWAI_SESSION_STAGE_FAILED"; return 1
  fi
  adb shell am force-stop "$PKG" >/dev/null 2>&1 || true
  # Preserve existing data until staged contents are complete.
  if ! adb shell "test -d /data/user/0/$PKG && mv /data/user/0/$PKG '$staging/backup' || true; mv '$staging/unpacked/$PKG' /data/user/0/$PKG" >/dev/null 2>&1; then
    adb shell "test -d '$staging/backup' && mv '$staging/backup' /data/user/0/$PKG || true" >/dev/null 2>&1 || true
    log "KWAI_SESSION_APPLY_FAILED"; return 1
  fi
  adb shell "restorecon -RF /data/user/0/$PKG" >/dev/null 2>&1 || true
  log "KWAI_SESSION_RESTORED"
}

save_state(){
  [ -n "${KWAI_PASSWORD:-}" ] || { log "KWAI_SESSION_KEY_MISSING"; return 1; }
  root_ready || { log "KWAI_SESSION_ROOT_UNAVAILABLE"; return 1; }
  local tmp archive
  tmp="${STATE_FILE}.tmp"
  archive="$(mktemp)"
  trap 'rm -f "$archive" "$tmp"' RETURN
  adb shell am force-stop "$PKG" >/dev/null 2>&1 || true
  if ! adb exec-out "tar -C /data/user/0 -cpf - $PKG" >"$archive" 2>/dev/null; then
    log "KWAI_SESSION_ARCHIVE_FAILED"; return 1
  fi
  if ! tar -tf "$archive" >/dev/null 2>&1; then
    log "KWAI_SESSION_ARCHIVE_INVALID"; return 1
  fi
  if ! openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -pass env:KWAI_PASSWORD -in "$archive" -out "$tmp"; then
    log "KWAI_SESSION_ENCRYPT_FAILED"; return 1
  fi
  test -s "$tmp" || return 1
  mv "$tmp" "$STATE_FILE"
  chmod 600 "$STATE_FILE"
  log "KWAI_SESSION_SAVED_ENCRYPTED"
}

case "${1:-}" in
  restore) restore_state ;;
  save) save_state ;;
  *) echo "usage: $0 {restore|save}" >&2; exit 2 ;;
esac
