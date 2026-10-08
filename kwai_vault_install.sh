#!/usr/bin/env bash
set -Eeuo pipefail
REPORT=kwai-vault-install-status.txt
: > "$REPORT"
log(){ echo "$*" | tee -a "$REPORT"; }
# HOT-PATH CONTRACT: no store UI/browser/package acquisition here.
# Install the complete compatible split set from the validated vault. Installing
# only base + one DFM left Kwai in the permanent "Resource downloading 5%" state.
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

selected_abi=""
for abi in arm64_v8a armeabi_v7a x86_64 x86; do
  if echo "$ABI" | tr '-' '_' | grep -qw "$abi"; then selected_abi="$abi"; break; fi
done
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
log "SELECTED_DENSITY=$bucket"

mapfile -t ALL_APKS < <(find kwai-vault -type f -name '*.apk' | sort)
log "VAULT_APK_COUNT=${#ALL_APKS[@]}"
printf 'VAULT_APKS=' >>"$REPORT"; printf '%s ' "${ALL_APKS[@]##*/}" >>"$REPORT"; printf '\n' >>"$REPORT"

APKS=("$BASE")
for p in "${ALL_APKS[@]}"; do
  [ "$p" = "$BASE" ] && continue
  name="${p##*/}"

  # Keep only the ABI split compatible with this emulator/native bridge.
  if [[ "$name" =~ (^|\.)config\.(arm64_v8a|armeabi_v7a|x86_64|x86)\.apk$ ]]; then
    [[ "$name" =~ (^|\.)config\.${selected_abi}\.apk$ ]] || continue
  fi

  # Keep only the density split matching the emulator. Feature-specific density
  # splits are filtered the same way; language and feature APKs remain included.
  if [[ "$name" =~ (^|\.)config\.(ldpi|mdpi|hdpi|xhdpi|xxhdpi|xxxhdpi)\.apk$ ]]; then
    [[ "$name" =~ (^|\.)config\.${bucket}\.apk$ ]] || continue
  fi

  APKS+=("$p")
done

log "SELECTED_SPLIT_COUNT=${#APKS[@]}"
printf 'SELECTED_SPLITS=' >>"$REPORT"; printf '%s ' "${APKS[@]##*/}" >>"$REPORT"; printf '\n' >>"$REPORT"
log "STEP_INSTALL_MULTIPLE_START"
timeout 240 adb install-multiple -r "${APKS[@]}" >>"$REPORT" 2>&1 || { rc=$?; log "FAIL_INSTALL_MULTIPLE_RC=$rc"; exit 41; }
log "STEP_INSTALL_MULTIPLE_OK"
log "STEP_PM_PATH_START"
timeout 30 adb shell pm path com.kwai.video >>"$REPORT" 2>&1 || { rc=$?; log "FAIL_PACKAGE_NOT_PRESENT_RC=$rc"; exit 42; }
log "STEP_PM_PATH_OK"
log "INSTALLED_PACKAGE_PATHS_START"
adb shell pm path com.kwai.video >>"$REPORT" 2>&1 || true
log "INSTALLED_PACKAGE_PATHS_END"
log "STEP_KWAI_LAUNCH_START"
timeout 30 adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >>"$REPORT" 2>&1 || { rc=$?; log "FAIL_KWAI_LAUNCH_RC=$rc"; exit 43; }
log "STEP_KWAI_LAUNCH_OK"
sleep 2
adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' >>"$REPORT" 2>&1 || true
log KWAI_LAUNCHED
