#!/usr/bin/env bash
set -Eeuo pipefail

LABEL="${1:-env}"
ROOT="evidence/fast-$LABEL"
mkdir -p "$ROOT"

adb wait-for-device
DEVICE_ABI="$(adb shell getprop ro.product.cpu.abi | tr -d '\r[:space:]')"
DEVICE_API="$(adb shell getprop ro.build.version.sdk | tr -d '\r[:space:]')"
printf 'label=%s api=%s abi=%s\n' "$LABEL" "$DEVICE_API" "$DEVICE_ABI" | tee "$ROOT/context.txt"

mapfile -t ALL_APKS < <(find /tmp/xout -type f -name '*.apk' -print | sort)
((${#ALL_APKS[@]} > 0)) || { echo NO_APKS_AT_INSTALL | tee "$ROOT/final.txt"; exit 79; }
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
    x86:*x86_64*.apk) continue ;;
    x86_64:*arm*.apk|x86:*arm*.apk) continue ;;
    x86_64:*x86_64*.apk|x86_64:*x86*.apk|x86:*x86*.apk|*:*) FILTERED+=("$apk") ;;
  esac
done
[[ -n "$BASE" ]] || BASE="$(find /tmp/xout -maxdepth 1 -type f \( -name 'base.apk' -o -name 'com.twitter.android.apk' \) -print -quit)"
[[ -n "$BASE" ]] || { echo BASE_APK_NOT_FOUND | tee "$ROOT/final.txt"; exit 83; }

# Ensure base is first and unique.
TMP=("$BASE")
for apk in "${FILTERED[@]}"; do
  [[ "$apk" == "$BASE" ]] && continue
  TMP+=("$apk")
done
FILTERED=("${TMP[@]}")
printf '%s\n' "${FILTERED[@]}" > "$ROOT/filtered-apks.txt"

run_session_install() {
  local out session_id idx apk size remote
  set +e
  out="$(adb shell pm install-create -r 2>&1)"
  local rc=$?
  set -e
  printf '%s\n' "$out"
  [[ "$rc" -eq 0 ]] || return "$rc"
  session_id="$(printf '%s' "$out" | sed -n 's/.*\[\([0-9][0-9]*\)\].*/\1/p' | tail -1)"
  [[ -n "$session_id" ]] || return 88
  idx=0
  for apk in "${FILTERED[@]}"; do
    size="$(stat -c%s "$apk")"
    remote="/data/local/tmp/xfast-$LABEL-$idx.apk"
    adb push "$apk" "$remote" >/dev/null
    adb shell pm install-write -S "$size" "$session_id" "split$idx" "$remote"
    idx=$((idx+1))
  done
  adb shell pm install-commit "$session_id"
}

passed=0
for mode in 0 1 2 3; do
  T="$ROOT/test-$mode"
  mkdir -p "$T"
  adb shell pm uninstall com.twitter.android >/dev/null 2>&1 || true
  adb logcat -c || true

  set +e
  case "$mode" in
    0) adb install-multiple -r -d "${ALL_APKS[@]}" >"$T/install.txt" 2>&1 ;;
    1) adb install-multiple --no-streaming -r "${ALL_APKS[@]}" >"$T/install.txt" 2>&1 ;;
    2) adb install-multiple -r -g "${FILTERED[@]}" >"$T/install.txt" 2>&1 ;;
    3) run_session_install >"$T/install.txt" 2>&1 ;;
  esac
  irc=$?
  set -e
  echo "install_rc=$irc" >> "$T/install.txt"

  if [[ "$irc" -ne 0 ]]; then
    grep -Ei 'INSTALL_FAILED|Failure|Error|Exception|NO_MATCHING_ABIS|MISSING_SPLIT|INVALID_APK|OLDER_SDK|NEWER_SDK|VERSION_DOWNGRADE' "$T/install.txt" | tail -80 > "$T/classification.txt" || true
    echo FAIL_INSTALL | tee "$T/verdict.txt"
    continue
  fi

  adb shell pm path com.twitter.android > "$T/pm-path.txt" 2>&1 || true
  activity="$(adb shell cmd package resolve-activity --brief com.twitter.android 2>/dev/null | tr -d '\r' | tail -1 || true)"
  echo "$activity" > "$T/activity.txt"
  if [[ "$activity" == */* ]]; then
    adb shell am start -W -n "$activity" > "$T/launch.txt" 2>&1 || true
  else
    adb shell monkey -p com.twitter.android -c android.intent.category.LAUNCHER 1 > "$T/launch.txt" 2>&1 || true
  fi
  sleep 3
  pid1="$(adb shell pidof com.twitter.android 2>/dev/null | tr -d '\r' || true)"
  echo "$pid1" > "$T/pid-3s.txt"
  sleep 2
  pid2="$(adb shell pidof com.twitter.android 2>/dev/null | tr -d '\r' || true)"
  echo "$pid2" > "$T/pid-5s.txt"
  adb logcat -d | tail -2500 > "$T/logcat.txt" || true
  timeout 8 adb shell uiautomator dump /sdcard/x-fast.xml >/dev/null 2>&1 || true
  adb pull /sdcard/x-fast.xml "$T/window.xml" >/dev/null 2>&1 || true

  if [[ -n "$pid1" && -n "$pid2" ]]; then
    echo PASS_X_INSTALLED_AND_LAUNCHED | tee "$T/verdict.txt"
    passed=$((passed+1))
  else
    grep -Ei 'FATAL EXCEPTION|AndroidRuntime|Process: com.twitter.android|UnsatisfiedLinkError|NoClassDefFoundError|VerifyError|SIGSEGV|SIGABRT' "$T/logcat.txt" | tail -120 > "$T/crash.txt" || true
    echo FAIL_LAUNCH | tee "$T/verdict.txt"
  fi
done

printf 'passed=%s total=4\n' "$passed" | tee "$ROOT/summary.txt"
[[ "$passed" -gt 0 ]]
