#!/usr/bin/env bash
set -Eeuo pipefail
REPORT=anthares-native-executor-status.txt
: > "$REPORT"
log(){ echo "$*" | tee -a "$REPORT"; }

export ANDROID_HOME="${ANDROID_HOME:-$ANDROID_SDK_ROOT}"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"

log ANTHARES_EXECUTOR=V1
log EXECUTOR_BACKEND=RAW_ANDROID_SDK

test -e /dev/kvm || { log FAIL_NO_KVM; exit 20; }
sudo chmod 666 /dev/kvm

yes | sdkmanager --licenses >/dev/null 2>&1 || true
sdkmanager --install "platform-tools" "emulator" "system-images;android-30;google_apis;x86_64" >/dev/null

echo no | avdmanager create avd --force --name anthares_native_30 --package "system-images;android-30;google_apis;x86_64" --device "pixel_5" >/dev/null

nohup emulator -avd anthares_native_30 \
  -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader_indirect \
  -accel on -memory 2048 -cores 2 -camera-back none -camera-front none \
  > /tmp/anthares-emulator.log 2>&1 &
EMU_PID=$!
trap 'kill "$EMU_PID" 2>/dev/null || true' EXIT

timeout 180 adb wait-for-device
for _ in $(seq 1 90); do
  [[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]] && break
  sleep 2
done
[[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]] || { log FAIL_BOOT_TIMEOUT; exit 21; }
log ANDROID_BOOTED=1

curl -fsSL --retry 3 --connect-timeout 10 --max-time 180 \
  -o /tmp/kwai-vault.zip \
  https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/kwai-package-vault/kwai-vault.zip
printf '%s  %s\n' '96650454576a2cf5cc5e63d90011f0b60a03d2702605756f40cc934cd6ae5543' /tmp/kwai-vault.zip | sha256sum -c -
rm -rf /tmp/kwai-vault && mkdir -p /tmp/kwai-vault
unzip -q /tmp/kwai-vault.zip -d /tmp/kwai-vault

BASE="$(find /tmp/kwai-vault -type f \( -name 'com.kwai.video.apk' -o -name 'base.apk' \) | head -1)"
[[ -n "$BASE" ]] || { log FAIL_NO_BASE_APK; exit 30; }
ABI="$(adb shell getprop ro.product.cpu.abilist | tr -d '\r')"
BRIDGE="$(adb shell getprop ro.dalvik.vm.native.bridge | tr -d '\r')"
DENSITY="$(adb shell wm density | sed -n 's/.*: //p' | tail -1 | tr -d '\r')"
selected_abi=x86_64
if ! find /tmp/kwai-vault -type f -name '*config.x86_64.apk' | grep -q .; then
  if [[ -n "$BRIDGE" && "$BRIDGE" != "0" ]]; then selected_abi=arm64_v8a; else selected_abi=""; fi
fi
[[ -n "$selected_abi" ]] || { log FAIL_NO_COMPATIBLE_ABI; exit 31; }
case "$DENSITY" in
  ''|*[!0-9]*) bucket=xxhdpi ;;
  *) if (( DENSITY <= 140 )); then bucket=ldpi; elif (( DENSITY <= 200 )); then bucket=mdpi; elif (( DENSITY <= 260 )); then bucket=hdpi; elif (( DENSITY <= 360 )); then bucket=xhdpi; elif (( DENSITY <= 560 )); then bucket=xxhdpi; else bucket=xxxhdpi; fi ;;
esac
mapfile -t ALL < <(find /tmp/kwai-vault -type f -name '*.apk' | sort)
APKS=("$BASE")
for p in "${ALL[@]}"; do
  [[ "$p" == "$BASE" ]] && continue
  n="${p##*/}"
  if [[ "$n" =~ (^|\.)config\.(arm64_v8a|armeabi_v7a|x86_64|x86)\.apk$ ]] && [[ ! "$n" =~ (^|\.)config\.${selected_abi}\.apk$ ]]; then continue; fi
  if [[ "$n" =~ (^|\.)config\.(ldpi|mdpi|hdpi|xhdpi|xxhdpi|xxxhdpi)\.apk$ ]] && [[ ! "$n" =~ (^|\.)config\.${bucket}\.apk$ ]]; then continue; fi
  APKS+=("$p")
done
log SELECTED_SPLIT_COUNT=${#APKS[@]}
timeout 240 adb install-multiple -r "${APKS[@]}" >/tmp/anthares-install.log 2>&1 || { cat /tmp/anthares-install.log; log FAIL_INSTALL; exit 32; }
adb shell pm path com.kwai.video >/dev/null || { log FAIL_PACKAGE_NOT_PRESENT; exit 33; }
log KWAI_INSTALLED=1

adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 5
python3 -m anthares_native.surface_driver --attempts 18 --output anthares-native-surface.json
python3 - <<'PY'
import json
x=json.load(open('anthares-native-surface.json'))
assert x.get('auth_surface_reached') is True, x
print('ANTHARES_EXECUTOR_AUTH_SURFACE_REACHED=1')
PY
log AUTH_SURFACE_REACHED=1
