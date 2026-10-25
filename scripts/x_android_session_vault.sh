#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:?usage: x_android_session_vault.sh {export|import} FILE}"
FILE="${2:?vault file required}"
PKG="com.twitter.android"
KEY="${X_ANDROID_SESSION_KEY:?X_ANDROID_SESSION_KEY is required}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

adb root >/dev/null 2>&1 || true
adb wait-for-device

case "$MODE" in
  export)
    adb shell am force-stop "$PKG" || true
    adb exec-out "tar -C /data/data -czf - $PKG" > "$TMP/session.tgz"
    test -s "$TMP/session.tgz"
    gpg --batch --yes --pinentry-mode loopback --passphrase "$KEY" --symmetric --cipher-algo AES256 -o "$FILE" "$TMP/session.tgz"
    echo "X_SESSION_EXPORT_OK file=$FILE"
    ;;
  import)
    test -s "$FILE"
    gpg --batch --yes --pinentry-mode loopback --passphrase "$KEY" -o "$TMP/session.tgz" -d "$FILE"
    adb shell am force-stop "$PKG" || true
    adb push "$TMP/session.tgz" /data/local/tmp/x-session.tgz >/dev/null
    adb shell "rm -rf /data/data/$PKG && tar -C /data/data -xzf /data/local/tmp/x-session.tgz && rm -f /data/local/tmp/x-session.tgz"
    uid="$(adb shell dumpsys package "$PKG" | sed -n 's/.*userId=\([0-9]*\).*/\1/p' | head -1 | tr -d '\r')"
    test -n "$uid"
    adb shell "chown -R $uid:$uid /data/data/$PKG && restorecon -RF /data/data/$PKG" || true
    echo "X_SESSION_IMPORT_OK uid=$uid"
    ;;
  *) exit 2 ;;
esac
