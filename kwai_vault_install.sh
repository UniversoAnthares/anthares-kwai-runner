#!/usr/bin/env bash
set -Eeuo pipefail
REPORT=kwai-vault-install-status.txt
: > "$REPORT"
log(){ echo "$*" | tee -a "$REPORT"; }
# HOT-PATH CONTRACT: no store UI/browser/package acquisition here.
# acceptance-revision: 3-arm64-vault
log "STEP_ADB_WAIT_START"
timeout 30 adb wait-for-device || { log FAIL_ADB_WAIT_TIMEOUT; exit 20; }
log "STEP_ADB_WAIT_OK"
[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] || { log FAIL_ANDROID_NOT_READY; exit 21; }
ABI="$(adb shell getprop ro.product.cpu.abilist | tr -d '\r')"
DENSITY="$(adb shell wm density | sed -n 's/.*: //p' | tail -1 | tr -d '\r')"
BRIDGE="$(adb shell getprop ro.dalvik.vm.native.bridge | tr -d '\r')"
log "DEVICE_ABI=$ABI"
log "NATIVE_BRIDGE=$BRIDGE"
log "DEVICE_DENSITY=$DENSITY"
BASE="$(find kwai-vault -type f -name 'com.kwai.video.apk' | head -1)"
[ -n "$BASE" ] || BASE="$(find kwai-vault -type f -name 'base.apk' | head -1)"
[ -n "$BASE" ] || { log FAIL_NO_BASE_APK; exit 40; }
APKS=("$BASE")
# Proven install set for this validated bundle: base + dfm_ug + ABI + density.
p="$(find kwai-vault -type f -name 'dfm_ug.apk' | head -1 || true)"
[ -z "$p" ] || APKS+=("$p")
selected_abi=""
# This validated vault is ARM64. On x86 hosts, only use it when a native bridge is present.
for abi in arm64_v8a armeabi_v7a x86_64 x86; do
  if echo "$ABI" | tr '-' '_' | grep -qw "$abi"; then selected_abi="$abi"; break; fi
done
# Never mix a foreign ABI. ARM64 is permitted on x86_64 only when Android exposes a native bridge.
has_selected=""
[ -z "$selected_abi" ] || has_selected="$(find kwai-vault -type f \( -name "config.$selected_abi.apk" -o -name "*.config.$selected_abi.apk" \) -print -quit 2>/dev/null)"
if [ -z "$has_selected" ]; then
  if [ -n "$BRIDGE" ] && [ "$BRIDGE" != "0" ] && [ -n "$(find kwai-vault -type f \( -name 'config.arm64_v8a.apk' -o -name '*.config.arm64_v8a.apk' \) -print -quit)" ]; then
    selected_abi=arm64_v8a
  else
    log "FAIL_NO_COMPATIBLE_ABI_SPLIT=$selected_abi BRIDGE=$BRIDGE"
    exit 44
  fi
fi
p="$(find kwai-vault -type f \( -name "config.$selected_abi.apk" -o -name "*.config.$selected_abi.apk" \) | head -1 || true)"
[ -z "$p" ] || APKS+=("$p")
log "SELECTED_ABI=$selected_abi"
case "$DENSITY" in
  ''|*[!0-9]*) bucket=xxhdpi ;;
  *) if [ "$DENSITY" -le 140 ]; then bucket=ldpi
     elif [ "$DENSITY" -le 200 ]; then bucket=mdpi
     elif [ "$DENSITY" -le 260 ]; then bucket=hdpi
     elif [ "$DENSITY" -le 360 ]; then bucket=xhdpi
     elif [ "$DENSITY" -le 560 ]; then bucket=xxhdpi
     else bucket=xxxhdpi; fi ;;
esac
p="$(find kwai-vault -type f -name "config.$bucket.apk" | head -1 || true)"
[ -z "$p" ] || APKS+=("$p")
log "SELECTED_SPLITS=$(printf '%s ' "${APKS[@]##*/}")"
log "STEP_INSTALL_MULTIPLE_START"
timeout 180 adb install-multiple -r "${APKS[@]}" >>"$REPORT" 2>&1 || { rc=$?; log "FAIL_INSTALL_MULTIPLE_RC=$rc"; exit 41; }
log "STEP_INSTALL_MULTIPLE_OK"
log "STEP_PM_PATH_START"
timeout 30 adb shell pm path com.kwai.video >>"$REPORT" 2>&1 || { rc=$?; log "FAIL_PACKAGE_NOT_PRESENT_RC=$rc"; exit 42; }
log "STEP_PM_PATH_OK"
log "STEP_KWAI_LAUNCH_START"
timeout 30 adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >>"$REPORT" 2>&1 || { rc=$?; log "FAIL_KWAI_LAUNCH_RC=$rc"; exit 43; }
log "STEP_KWAI_LAUNCH_OK"
sleep 2
adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' >>"$REPORT" 2>&1 || true
log KWAI_LAUNCHED
