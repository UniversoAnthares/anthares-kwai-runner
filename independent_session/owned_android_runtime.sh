#!/usr/bin/env bash
set -euo pipefail
: "${ANDROID_HOME:=${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
export ANDROID_HOME
export ANDROID_AVD_HOME="${RUNNER_TEMP:-/tmp}/anthares-avds"
mkdir -p "$ANDROID_AVD_HOME"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$PATH"
scenario="${ANDROID_SCENARIO:-1}"
[[ "$scenario" =~ ^([1-9]|1[0-9]|20)$ ]] || exit 2
echo "SCENARIO=$scenario"
command -v sdkmanager >/dev/null || { echo SDKMANAGER_MISSING; exit 2; }
command -v avdmanager >/dev/null || { echo AVDMANAGER_MISSING; exit 2; }
[[ -r /dev/kvm && -w /dev/kvm ]] || { echo KVM_UNAVAILABLE; exit 2; }
# All scenarios exercise a different boot or host parameter.
api=35; image=google_apis; device=pixel_6; gpu=swiftshader_indirect
cores=2; memory=2048; disk=2048; boot_timeout=80
extra=()
case "$scenario" in
  1) : ;;
  2) api=34 ;;
  3) image=default ;;
  4) device=pixel_5 ;;
  5) device=pixel_4 ;;
  6) gpu=off ;;
  7) gpu=auto ;;
  8) cores=1 ;;
  9) cores=4 ;;
  10) memory=1536 ;;
  11) memory=3072 ;;
  12) disk=1024 ;;
  13) disk=4096 ;;
  14) extra+=(-no-snapshot) ;;
  15) extra+=(-no-boot-anim) ;;
  16) extra+=(-no-metrics) ;;
  17) extra+=(-netdelay none) ;;
  18) extra+=(-netspeed full) ;;
  19) extra+=(-camera-back none) ;;
  20) extra+=(-camera-front none) ;;
esac
sdk_image="system-images;android-$api;$image;x86_64"
echo "SDK_IMAGE=$sdk_image DEVICE=$device GPU=$gpu CORES=$cores MEMORY=$memory DISK=$disk"
timeout 125s sdkmanager --install 'platform-tools' 'emulator' "$sdk_image" >/dev/null || { echo SDK_INSTALL_FAILED; exit 1; }
command -v emulator >/dev/null || { echo EMULATOR_INSTALL_FAILED; exit 1; }
printf 'no\n' | timeout 20s avdmanager create avd -n anthares_owned -k "$sdk_image" -d "$device" --force -p "$ANDROID_AVD_HOME/anthares_owned.avd" >/dev/null || { echo AVD_CREATE_FAILED; exit 1; }
[[ -f "$ANDROID_AVD_HOME/anthares_owned.ini" ]] || { echo AVD_INI_MISSING; ls -la "$ANDROID_AVD_HOME"; exit 1; }
emulator -list-avds | grep -qx anthares_owned || { echo AVD_NOT_DISCOVERABLE; exit 1; }
timeout 10s emulator -accel-check || { echo ACCELERATION_FAILED; exit 1; }
emulator -avd anthares_owned -no-window -no-audio -no-boot-anim -no-snapshot-save -gpu "$gpu" -cores "$cores" -memory "$memory" -partition-size "$disk" "${extra[@]}" -port 5554 >/tmp/anthares-emulator.log 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true' EXIT
timeout 25s adb wait-for-device || { echo ADB_CONNECT_TIMEOUT; tail -30 /tmp/anthares-emulator.log; exit 1; }
ready=0
for i in $(seq 1 40); do
  if [[ "$(timeout 3s adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == 1 ]]; then ready=1; break; fi
  kill -0 "$pid" 2>/dev/null || { echo EMULATOR_EXITED; tail -30 /tmp/anthares-emulator.log; exit 1; }
  sleep 2
done
[[ "$ready" == 1 ]] || { echo ANDROID_BOOT_TIMEOUT; tail -30 /tmp/anthares-emulator.log; exit 1; }
actual="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
[[ "$actual" == "$api" ]] || { echo "SDK_MISMATCH:$actual"; exit 1; }
echo "OWN_ANDROID_RUNTIME_BOOT_VERIFIED scenario=$scenario sdk=$actual"
# Stage 2: real official APK installation and foreground launch, never credentials.
if [[ -d kwai-vault ]]; then
  timeout 95s bash kwai_vault_install.sh || { echo KWAI_INSTALL_OR_LAUNCH_FAILED; exit 1; }
  adb shell pm path com.kwai.video | grep -q package: || { echo KWAI_PACKAGE_NOT_INSTALLED; exit 1; }
  echo "KWAI_OFFICIAL_APK_INSTALLED_AND_LAUNCHED scenario=$scenario"
fi
