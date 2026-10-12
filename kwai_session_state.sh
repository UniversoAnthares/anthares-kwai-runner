#!/usr/bin/env bash
set -Eeuo pipefail

ACCOUNT_ID="${KWAI_ACCOUNT_ID:-primary}"
case "$ACCOUNT_ID" in primary|secondary) ;; *) echo "invalid KWAI_ACCOUNT_ID" >&2; exit 2 ;; esac
if [ -n "${KWAI_SESSION_FILE:-}" ]; then
  STATE_FILE="$KWAI_SESSION_FILE"
elif [ "$ACCOUNT_ID" = primary ]; then
  STATE_FILE="kwai-session.enc"
else
  STATE_FILE="kwai-session-secondary.enc"
fi
PKG="com.kwai.video"

log(){ printf '%s\n' "$*"; }

root_ready(){
  adb root >/dev/null 2>&1 || true
  adb wait-for-device
  adb shell id 2>/dev/null | grep -q 'uid=0'
}

restore_state(){
  [ -s "$STATE_FILE" ] || { log "KWAI_SESSION_CACHE_MISS"; return 1; }
  [ -n "${KWAI_SESSION_ENCRYPTION_KEY:-}" ] || { log "KWAI_SESSION_KEY_MISSING"; return 1; }
  root_ready || { log "KWAI_SESSION_ROOT_UNAVAILABLE"; return 1; }
  local archive staging
  archive="$(mktemp)"
  staging="/data/local/tmp/kwai-restore-$$"
  trap 'rm -f "$archive"; adb shell rm -rf "$staging" >/dev/null 2>&1 || true' RETURN
  if ! openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:KWAI_SESSION_ENCRYPTION_KEY -in "$STATE_FILE" -out "$archive" 2>/dev/null; then
    log "KWAI_SESSION_DECRYPT_FAILED"; return 1
  fi
  if ! python3 - "$archive" <<'PY'
import sys, tarfile
from pathlib import PurePosixPath
try:
    with tarfile.open(sys.argv[1]) as tf:
        members=tf.getmembers()
        if not members:
            raise ValueError("empty")
        for member in members:
            p=PurePosixPath(member.name)
            if (p.is_absolute() or ".." in p.parts or not p.parts
                    or p.parts[0]!="com.kwai.video"
                    or not (member.isfile() or member.isdir())):
                raise ValueError("unsafe archive member")
except (OSError, ValueError, tarfile.TarError):
    sys.exit(1)
PY
  then
    log "KWAI_SESSION_ARCHIVE_INVALID"; return 1
  fi
  adb shell mkdir -p "$staging"
  if ! adb push "$archive" "$staging/session.tar" >/dev/null 2>&1; then
    log "KWAI_SESSION_TRANSFER_FAILED"; return 1
  fi
  if ! adb shell "mkdir -p '$staging/unpacked' && tar -C '$staging/unpacked' -xpf '$staging/session.tar' && test -d '$staging/unpacked/$PKG'" >/dev/null 2>&1; then
    log "KWAI_SESSION_STAGE_FAILED"; return 1
  fi
  adb shell am force-stop "$PKG" >/dev/null 2>&1 || true
  if ! adb shell "test -d /data/user/0/$PKG && mv /data/user/0/$PKG '$staging/backup' || true; mv '$staging/unpacked/$PKG' /data/user/0/$PKG" >/dev/null 2>&1; then
    adb shell "test -d '$staging/backup' && mv '$staging/backup' /data/user/0/$PKG || true" >/dev/null 2>&1 || true
    log "KWAI_SESSION_APPLY_FAILED"; return 1
  fi
  adb shell "restorecon -RF /data/user/0/$PKG" >/dev/null 2>&1 || true
  log "KWAI_SESSION_RESTORED"
}

save_state(){
  # Existing Stage4 workflow already writes a non-secret proof file for the
  # winning identity candidate. Recover only that verified handle when the
  # caller did not export KWAI_EXPECTED_ACCOUNT, then re-prove it live below.
  if [ -z "${KWAI_EXPECTED_ACCOUNT:-}" ]; then
    local candidate proof_file
    for candidate in lucasrosalem universo.anthares; do
      proof_file="auth-${candidate}.txt"
      if [ -s "$proof_file" ] &&
         grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' "$proof_file" &&
         grep -qx 'KWAI_IDENTITY_PROFILE_MATCH=1' "$proof_file"; then
        export KWAI_EXPECTED_ACCOUNT="$candidate"
        log "KWAI_SESSION_IDENTITY_RECOVERED_FROM_PROOF"
        break
      fi
    done
  fi
  [ -n "${KWAI_EXPECTED_ACCOUNT:-}" ] || { log "KWAI_SESSION_IDENTITY_UNCONFIGURED"; return 1; }
  local proof
  proof="$(mktemp)"
  if ! python3 kwai_auth_probe.py >"$proof" 2>/dev/null ||
     ! grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' "$proof" ||
     ! grep -qx 'KWAI_IDENTITY_PROFILE_MATCH=1' "$proof"; then
    rm -f "$proof"
    log "KWAI_SESSION_SAVE_REFUSED_IDENTITY_UNVERIFIED"
    return 1
  fi
  rm -f "$proof"
  [ -n "${KWAI_SESSION_ENCRYPTION_KEY:-}" ] || { log "KWAI_SESSION_KEY_MISSING"; return 1; }
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
  if ! openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -pass env:KWAI_SESSION_ENCRYPTION_KEY -in "$archive" -out "$tmp"; then
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
