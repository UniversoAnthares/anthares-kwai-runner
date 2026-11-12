#!/usr/bin/env bash
set -Eeuo pipefail

VARIANT="${X_LOGIN_VARIANT:-1}"
MODE="${X_INSTALL_MODE:-0}"
ROOT="${EVIDENCE_DIR:-evidence/auth-${VARIANT}}"
mkdir -p "$ROOT"
export EVIDENCE_DIR="$ROOT/login"
mkdir -p "$EVIDENCE_DIR"

adb wait-for-device
DEVICE_ABI="$(adb shell getprop ro.product.cpu.abi | tr -d '\r[:space:]')"
DEVICE_API="$(adb shell getprop ro.build.version.sdk | tr -d '\r[:space:]')"
printf 'variant=%s install_mode=%s api=%s abi=%s input=%s wait=%s launch=%s\n' \
  "$VARIANT" "$MODE" "$DEVICE_API" "$DEVICE_ABI" \
  "${X_LOGIN_INPUT_BACKEND:-adb}" "${X_LOGIN_WAIT:-4}" "${X_LOGIN_LAUNCH_MODE:-0}" \
  | tee "$ROOT/context.txt"

mapfile -t ALL_APKS < <(find /tmp/xout -type f -name '*.apk' -print | sort)
((${#ALL_APKS[@]} > 0)) || { echo NO_APKS_AT_INSTALL | tee "$ROOT/verdict.txt"; exit 79; }
printf '%s\n' "${ALL_APKS[@]}" > "$ROOT/all-apks.txt"

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
AAPT=""
if [[ -n "$SDK_ROOT" && -d "$SDK_ROOT/build-tools" ]]; then
  AAPT="$(find "$SDK_ROOT/build-tools" -mindepth 2 -maxdepth 2 -type f -name aapt -print | sort -V | tail -1)"
fi
[[ -x "$AAPT" ]] || AAPT="$(command -v aapt || true)"

BASE=""
FILTERED=()
for apk in "${ALL_APKS[@]}"; do
  name="$(basename "$apk" | tr '[:upper:]' '[:lower:]')"
  split=""
  if [[ -x "$AAPT" ]]; then
    split="$($AAPT dump badging "$apk" 2>/dev/null | sed -n "s/^package:.* split='\([^']*\)'.*/\1/p" | head -1)"
  fi
  [[ -z "$split" ]] && BASE="$apk"
  case "$DEVICE_ABI:$name" in
    x86_64:*arm*.apk|x86:*arm*.apk) continue ;;
    x86:*x86_64*.apk) continue ;;
    *) FILTERED+=("$apk") ;;
  esac
done
[[ -n "$BASE" ]] || BASE="$(find /tmp/xout -maxdepth 1 -type f \( -name 'base.apk' -o -name 'com.twitter.android.apk' \) -print -quit)"
[[ -n "$BASE" ]] || { echo BASE_APK_NOT_FOUND | tee "$ROOT/verdict.txt"; exit 83; }

TMP=("$BASE")
for apk in "${FILTERED[@]}"; do
  [[ "$apk" == "$BASE" ]] && continue
  TMP+=("$apk")
done
FILTERED=("${TMP[@]}")
printf '%s\n' "${FILTERED[@]}" > "$ROOT/filtered-apks.txt"

session_install() {
  local out session_id idx apk size remote
  out="$(adb shell pm install-create -r 2>&1)"
  printf '%s\n' "$out"
  session_id="$(printf '%s' "$out" | sed -n 's/.*\[\([0-9][0-9]*\)\].*/\1/p' | tail -1)"
  [[ -n "$session_id" ]] || return 88
  idx=0
  for apk in "${FILTERED[@]}"; do
    size="$(stat -c%s "$apk")"
    remote="/data/local/tmp/xauth-${VARIANT}-${idx}.apk"
    adb push "$apk" "$remote" >/dev/null
    adb shell pm install-write -S "$size" "$session_id" "split$idx" "$remote"
    idx=$((idx+1))
  done
  adb shell pm install-commit "$session_id"
}

adb shell pm uninstall com.twitter.android >/dev/null 2>&1 || true
adb logcat -c || true
set +e
case "$MODE" in
  0) adb install-multiple -r -d "${ALL_APKS[@]}" >"$ROOT/install.txt" 2>&1 ;;
  1) adb install-multiple --no-streaming -r "${ALL_APKS[@]}" >"$ROOT/install.txt" 2>&1 ;;
  2) adb install-multiple -r -g "${FILTERED[@]}" >"$ROOT/install.txt" 2>&1 ;;
  3) session_install >"$ROOT/install.txt" 2>&1 ;;
  *) echo "INVALID_INSTALL_MODE=$MODE" >"$ROOT/install.txt"; false ;;
esac
IRC=$?
set -e
echo "install_rc=$IRC" >> "$ROOT/install.txt"

if [[ "$IRC" -ne 0 ]]; then
  grep -Ei 'INSTALL_FAILED|Failure|Error|Exception|NO_MATCHING_ABIS|MISSING_SPLIT|INVALID_APK|OLDER_SDK|NEWER_SDK|VERSION_DOWNGRADE' \
    "$ROOT/install.txt" | tail -100 > "$ROOT/install-classification.txt" || true
  echo FAIL_INSTALL | tee "$ROOT/verdict.txt"
  exit 81
fi

adb shell pm path com.twitter.android > "$ROOT/pm-path.txt" 2>&1
if ! grep -q '^package:' "$ROOT/pm-path.txt"; then
  echo FAIL_PACKAGE_NOT_INSTALLED | tee "$ROOT/verdict.txt"
  exit 82
fi

set +e
python3 scripts/x_android_login_ui.py 2>&1 | tee "$ROOT/login-run.txt"
LRC=${PIPESTATUS[0]}
set -e

echo "login_rc=$LRC" >> "$ROOT/login-run.txt"
adb shell dumpsys package com.twitter.android | grep -E 'versionName=|primaryCpuAbi=' > "$ROOT/package.txt" 2>&1 || true
adb shell dumpsys activity activities > "$ROOT/activities.txt" 2>&1 || true
adb logcat -d | tail -3500 > "$ROOT/logcat.txt" 2>&1 || true

if [[ "$LRC" -eq 0 ]] && grep -q 'VERDICT=X_ANDROID_AUTHENTICATED' "$ROOT/login-run.txt"; then
  echo PASS_X_ANDROID_AUTHENTICATED | tee "$ROOT/verdict.txt"
  exit 0
fi

if [[ -f "$EVIDENCE_DIR/verdict.txt" ]]; then
  printf 'FAIL_X_AUTH: ' | tee "$ROOT/verdict.txt"
  cat "$EVIDENCE_DIR/verdict.txt" | tee -a "$ROOT/verdict.txt"
else
  echo FAIL_X_AUTH_UNCLASSIFIED | tee "$ROOT/verdict.txt"
fi
exit "$LRC"
