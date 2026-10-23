#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-0}"
VARIANT="${2:-0}"
mkdir -p evidence

adb wait-for-device
for _ in $(seq 1 60); do
  state="$(adb get-state 2>/dev/null || true)"
  boot="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  [[ "$state" == device && "$boot" == 1 ]] && break
  sleep 2
done

adb shell getprop ro.build.version.sdk | tee evidence/device-api.txt
adb shell getprop ro.product.cpu.abi | tee evidence/device-abi.txt
adb shell getprop ro.product.cpu.abilist | tee evidence/device-abilist.txt || true
adb shell wm density | tee evidence/device-density.txt || true
adb shell wm size | tee evidence/device-size.txt || true

DEVICE_ABI="$(adb shell getprop ro.product.cpu.abi | tr -d '\r[:space:]')"
DEVICE_API="$(adb shell getprop ro.build.version.sdk | tr -d '\r[:space:]')"
printf 'variant=%s mode=%s device_api=%s device_abi=%s\n' "$VARIANT" "$MODE" "$DEVICE_API" "$DEVICE_ABI" | tee evidence/install-context.txt

adb shell pm uninstall com.twitter.android >/dev/null 2>&1 || true
adb logcat -c || true

mapfile -t ALL_APKS < <(find /tmp/xout -type f -name '*.apk' -print | sort)
((${#ALL_APKS[@]} > 0)) || { echo NO_APKS_AT_INSTALL | tee evidence/install-verdict.txt; exit 79; }
printf '%s\n' "${ALL_APKS[@]}" > evidence/all-apks.txt

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
AAPT=""
if [[ -n "$SDK_ROOT" && -d "$SDK_ROOT/build-tools" ]]; then
  AAPT="$(find "$SDK_ROOT/build-tools" -mindepth 2 -maxdepth 2 -type f -name aapt -print | sort -V | tail -1)"
fi
[[ -x "$AAPT" ]] || AAPT="$(command -v aapt || true)"

BASE=""
SELECTED=()
for apk in "${ALL_APKS[@]}"; do
  name="$(basename "$apk" | tr '[:upper:]' '[:lower:]')"
  split=""
  if [[ -x "$AAPT" ]]; then
    split="$($AAPT dump badging "$apk" 2>/dev/null | sed -n "s/^package:.* split='\([^']*\)'.*/\1/p" | head -1)"
  fi
  if [[ -z "$split" ]]; then
    BASE="$apk"
  fi
  case "$DEVICE_ABI:$name" in
    x86_64:*x86_64*.apk|x86:*config.x86.apk|x86:*x86.apk) SELECTED+=("$apk") ;;
    x86_64:*config.x86.apk|x86_64:*x86.apk) SELECTED+=("$apk") ;;
    *:*config.en*.apk|*:*config.pt*.apk|*:*mdpi*.apk|*:*hdpi*.apk|*:*xhdpi*.apk|*:*xxhdpi*.apk|*:*xxxhdpi*.apk) SELECTED+=("$apk") ;;
  esac
done
[[ -n "$BASE" ]] || BASE="$(find /tmp/xout -maxdepth 1 -type f \( -name 'base.apk' -o -name 'com.twitter.android.apk' \) -print -quit)"
[[ -n "$BASE" ]] || { echo BASE_APK_NOT_FOUND | tee evidence/install-verdict.txt; exit 83; }

FILTERED=("$BASE")
for apk in "${SELECTED[@]}"; do
  [[ "$apk" == "$BASE" ]] && continue
  seen=0
  for cur in "${FILTERED[@]}"; do [[ "$cur" == "$apk" ]] && seen=1; done
  [[ "$seen" -eq 0 ]] && FILTERED+=("$apk")
done
printf '%s\n' "${FILTERED[@]}" > evidence/filtered-apks.txt

try_install() {
  local label="$1"; shift
  echo "===== $label =====" >> evidence/install-attempts.txt
  printf 'cmd:' >> evidence/install-attempts.txt
  printf ' %q' "$@" >> evidence/install-attempts.txt
  printf '\n' >> evidence/install-attempts.txt
  set +e
  "$@" >> evidence/install-attempts.txt 2>&1
  local rc=$?
  set -e
  echo "rc=$rc" >> evidence/install-attempts.txt
  return "$rc"
}

installed=0
install_all() {
  local flavor="$1"
  case "$flavor" in
    plain) try_install all_plain adb install-multiple -r "${ALL_APKS[@]}" ;;
    downgrade) try_install all_downgrade adb install-multiple -r -d "${ALL_APKS[@]}" ;;
    nostream) try_install all_nostream adb install-multiple --no-streaming -r "${ALL_APKS[@]}" ;;
    grant) try_install all_grant adb install-multiple -r -g "${ALL_APKS[@]}" ;;
  esac
}
install_filtered() {
  local flavor="$1"
  case "$flavor" in
    plain) try_install filtered_plain adb install-multiple -r "${FILTERED[@]}" ;;
    downgrade) try_install filtered_downgrade adb install-multiple -r -d "${FILTERED[@]}" ;;
    nostream) try_install filtered_nostream adb install-multiple --no-streaming -r "${FILTERED[@]}" ;;
    grant) try_install filtered_grant adb install-multiple -r -g "${FILTERED[@]}" ;;
  esac
}

case "$MODE" in
  0) order=(plain nostream grant downgrade) ;;
  1) order=(nostream plain downgrade grant) ;;
  2) order=(grant plain nostream downgrade) ;;
  3) order=(downgrade nostream plain grant) ;;
  *) order=(plain nostream grant downgrade) ;;
esac

for flavor in "${order[@]}"; do
  if install_all "$flavor"; then installed=1; break; fi
  adb shell pm uninstall com.twitter.android >/dev/null 2>&1 || true
done

if [[ "$installed" -ne 1 && "${#FILTERED[@]}" -gt 1 ]]; then
  for flavor in "${order[@]}"; do
    if install_filtered "$flavor"; then installed=1; break; fi
    adb shell pm uninstall com.twitter.android >/dev/null 2>&1 || true
  done
fi

if [[ "$installed" -ne 1 ]]; then
  # Last-resort session installer. This avoids adb install-multiple transport quirks.
  set +e
  session_out="$(adb shell pm install-create -r 2>&1)"
  session_rc=$?
  set -e
  echo "$session_out" >> evidence/install-attempts.txt
  session_id="$(printf '%s' "$session_out" | sed -n 's/.*\[\([0-9][0-9]*\)\].*/\1/p' | tail -1)"
  if [[ "$session_rc" -eq 0 && -n "$session_id" ]]; then
    idx=0
    session_ok=1
    for apk in "${FILTERED[@]}"; do
      size="$(stat -c%s "$apk")"
      remote="/data/local/tmp/xsplit-$VARIANT-$idx.apk"
      if ! adb push "$apk" "$remote" >> evidence/install-attempts.txt 2>&1; then session_ok=0; break; fi
      if ! adb shell pm install-write -S "$size" "$session_id" "split$idx" "$remote" >> evidence/install-attempts.txt 2>&1; then session_ok=0; break; fi
      idx=$((idx+1))
    done
    if [[ "$session_ok" -eq 1 ]] && adb shell pm install-commit "$session_id" >> evidence/install-attempts.txt 2>&1; then
      installed=1
    else
      adb shell pm install-abandon "$session_id" >/dev/null 2>&1 || true
    fi
  fi
fi

if [[ "$installed" -ne 1 ]]; then
  grep -E 'INSTALL_FAILED|Failure|Error|Exception|NO_MATCHING_ABIS|MISSING_SPLIT|OLDER_SDK|NEWER_SDK|INVALID_APK|VERSION_DOWNGRADE' evidence/install-attempts.txt | tail -200 > evidence/install-classification.txt || true
  echo ALL_INSTALL_STRATEGIES_FAILED | tee evidence/install-verdict.txt
  exit 80
fi

adb shell pm path com.twitter.android | tee evidence/pm-path.txt
adb shell dumpsys package com.twitter.android | grep -E 'versionName=|versionCode=|primaryCpuAbi=|secondaryCpuAbi=' | tee evidence/package.txt || true

# Normalize the emulator before first launch.
adb shell settings put global animator_duration_scale 0 >/dev/null 2>&1 || true
adb shell settings put global transition_animation_scale 0 >/dev/null 2>&1 || true
adb shell settings put global window_animation_scale 0 >/dev/null 2>&1 || true
adb shell am force-stop com.twitter.android >/dev/null 2>&1 || true

activity="$(adb shell cmd package resolve-activity --brief com.twitter.android 2>/dev/null | tr -d '\r' | tail -1 || true)"
echo "resolved_activity=$activity" | tee evidence/activity.txt
if [[ "$activity" == */* ]]; then
  adb shell am start -W -n "$activity" | tee evidence/launch-primary.txt || true
else
  adb shell monkey -p com.twitter.android -c android.intent.category.LAUNCHER 1 | tee evidence/launch-primary.txt || true
fi
sleep 6
pid="$(adb shell pidof com.twitter.android 2>/dev/null | tr -d '\r' || true)"
if [[ -z "$pid" ]]; then
  adb shell monkey -p com.twitter.android -c android.intent.category.LAUNCHER 1 | tee evidence/launch-retry.txt || true
  sleep 6
  pid="$(adb shell pidof com.twitter.android 2>/dev/null | tr -d '\r' || true)"
fi

echo "$pid" | tee evidence/pid.txt
adb logcat -d | tail -5000 > evidence/logcat-tail.txt || true
adb shell dumpsys activity activities > evidence/activities.txt || true
adb shell dumpsys window windows > evidence/windows.txt || true
adb shell uiautomator dump /sdcard/x-window.xml >/dev/null 2>&1 || true
adb pull /sdcard/x-window.xml evidence/x-window.xml >/dev/null 2>&1 || true

if [[ -z "$pid" ]]; then
  grep -E 'FATAL EXCEPTION|AndroidRuntime|Process: com.twitter.android|UnsatisfiedLinkError|NoClassDefFoundError|VerifyError|SIGSEGV|SIGABRT' evidence/logcat-tail.txt | tail -250 > evidence/crash-classification.txt || true
  echo X_DID_NOT_STAY_RUNNING | tee evidence/install-verdict.txt
  exit 81
fi

sleep 5
pid2="$(adb shell pidof com.twitter.android 2>/dev/null | tr -d '\r' || true)"
echo "$pid2" | tee evidence/pid-after-5s.txt
if [[ -z "$pid2" ]]; then
  grep -E 'FATAL EXCEPTION|AndroidRuntime|Process: com.twitter.android|UnsatisfiedLinkError|NoClassDefFoundError|VerifyError|SIGSEGV|SIGABRT' evidence/logcat-tail.txt | tail -250 > evidence/crash-classification.txt || true
  echo X_EXITED_AFTER_INITIAL_LAUNCH | tee evidence/install-verdict.txt
  exit 82
fi

echo X_INSTALLED_AND_LAUNCHED | tee evidence/install-verdict.txt
