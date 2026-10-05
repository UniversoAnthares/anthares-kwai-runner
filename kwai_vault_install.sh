#!/usr/bin/env bash
set -Eeuo pipefail
REPORT=kwai-vault-install-status.txt
: > "$REPORT"
log(){ echo "$*" | tee -a "$REPORT"; }
# HOT-PATH CONTRACT: no store UI/browser/package acquisition here.
# acceptance-revision: 3-arm64-vault
adb wait-for-device
[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] || { log FAIL_ANDROID_NOT_READY; exit 21; }
ABI="$(adb shell getprop ro.product.cpu.abilist | tr -d '\r')"
DENSITY="$(adb shell wm density | sed -n 's/.*: //p' | tail -1 | tr -d '\r')"
BRIDGE="$(adb shell getprop ro.dalvik.vm.native.bridge | tr -d '\r')"
log "DEVICE_ABI=$ABI"
log "NATIVE_BRIDGE=$BRIDGE"
log "DEVICE_DENSITY=$DENSITY"
BASE="$(find kwai-vault -type f \( -name 'base.apk' -o -name 'com.kwai.video.apk' \) | head -1)"
[ -n "$BASE" ] || { log FAIL_NO_BASE_APK; exit 40; }
APKS=("$BASE")
# Include non-configuration feature splits, but never install a foreign ABI split.
while IFS= read -r p; do
  n="$(basename "$p")"
  case "$n" in
    base.apk|com.kwai.video.apk|config.*) ;;
    *) APKS+=("$p") ;;
  esac
done < <(find kwai-vault -type f -name '*.apk' | sort)
selected_abi=""
for abi in x86_64 x86 arm64_v8a armeabi_v7a; do
  if echo "$ABI" | tr '-' '_' | grep -qw "$abi"; then selected_abi="$abi"; break; fi
done
# Google APIs x86_64 images can expose Google's native ARM bridge. When the vault has
# no x86 split, use arm64 through that bridge instead of dropping required native libs.
if [ -z "$(find kwai-vault -type f -name "config.$selected_abi.apk" -print -quit 2>/dev/null)" ] && [ -n "$BRIDGE" ] && [ "$BRIDGE" != "0" ]; then
  [ -z "$(find kwai-vault -type f -name 'config.arm64_v8a.apk' -print -quit)" ] || selected_abi=arm64_v8a
fi
p="$(find kwai-vault -type f -name "config.$selected_abi.apk" | head -1 || true)"
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
adb install-multiple -r "${APKS[@]}" >>"$REPORT" 2>&1 || { log FAIL_INSTALL_MULTIPLE; exit 41; }
adb shell pm path com.kwai.video >>"$REPORT" 2>&1 || { log FAIL_PACKAGE_NOT_PRESENT; exit 42; }
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >>"$REPORT" 2>&1 || { log FAIL_KWAI_LAUNCH; exit 43; }
sleep 2
adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' >>"$REPORT" 2>&1 || true
log KWAI_LAUNCHED
