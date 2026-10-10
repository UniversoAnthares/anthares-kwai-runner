#!/usr/bin/env bash
set -Eeuo pipefail
export ANDROID_HOME="${ANDROID_HOME:-$HOME/android-sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
if [[ ! -r /dev/kvm || ! -w /dev/kvm ]]; then echo 'ANTHARES_KVM=UNAVAILABLE'; exit 3; fi
mkdir -p "$ANDROID_HOME/cmdline-tools/latest"
if ! command -v sdkmanager >/dev/null; then
  curl -fLsS --retry 3 --max-time 120 https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip -o /tmp/anthares-tools.zip
  mkdir -p /tmp/anthares-tools
  unzip -q /tmp/anthares-tools.zip -d /tmp/anthares-tools
  mv /tmp/anthares-tools/cmdline-tools/* "$ANDROID_HOME/cmdline-tools/latest/"
fi
yes | sdkmanager --licenses >/dev/null || true
sdkmanager 'platform-tools' 'emulator' 'system-images;android-35;google_apis;x86_64'
avdmanager create avd --force -n anthares_android -k 'system-images;android-35;google_apis;x86_64' --device pixel_5 --sdcard 512M </dev/null
avd_rc=$?
if [[ $avd_rc -ne 0 || ! -f "$HOME/.android/avd/anthares_android.ini" ]]; then
  echo "ANTHARES_AVD_CREATION_FAILED=$avd_rc"
  exit 8
fi
echo 'ANTHARES_AVD_CREATED=1'
ls -l "$HOME/.android/avd/" || true
case "${ANTHARES_BOOT_VARIANT:-1}" in
  1) extra=(-memory 1536 -cores 2) ;;
  2) extra=(-memory 2048 -cores 2) ;;
  3) extra=(-memory 3072 -cores 2) ;;
  4) extra=(-memory 1536 -cores 4) ;;
  5) extra=(-memory 2048 -cores 4) ;;
  6) extra=(-gpu swiftshader_indirect -memory 1536) ;;
  7) extra=(-gpu swiftshader_indirect -memory 2048) ;;
  8) extra=(-gpu off -memory 1536) ;;
  9) extra=(-gpu off -memory 2048) ;;
  10) extra=(-no-boot-anim -memory 1536) ;;
  11) extra=(-no-boot-anim -memory 2048) ;;
  12) extra=(-no-snapshot -memory 1536) ;;
  13) extra=(-no-snapshot -memory 2048) ;;
  14) extra=(-netfast -memory 1536) ;;
  15) extra=(-netfast -memory 2048) ;;
  16) extra=(-camera-back none -memory 1536) ;;
  17) extra=(-camera-front none -memory 1536) ;;
  18) extra=(-no-metrics -memory 1536) ;;
  19) extra=(-no-metrics -memory 2048) ;;
  20) extra=(-memory 4096 -cores 2) ;;
  *) echo 'ANTHARES_INVALID_VARIANT'; exit 9 ;;
esac
echo "ANTHARES_BOOT_VARIANT=${ANTHARES_BOOT_VARIANT:-1}"
emulator -avd anthares_android -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader_indirect -accel on "${extra[@]}" > /tmp/anthares-emulator.log 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true' EXIT
echo 'ANTHARES_ANDROID_WAIT_START=1'
if ! timeout 120s adb wait-for-device; then
  echo 'ANTHARES_ANDROID_ADB_TIMEOUT=1'
  tail -80 /tmp/anthares-emulator.log || true
  exit 6
fi
for i in $(seq 1 45); do
  if [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]]; then
    echo 'ANTHARES_ANDROID_BOOT=PASS'
    adb shell getprop ro.build.version.release
    exit 0
  fi
  kill -0 "$pid" 2>/dev/null || { tail -50 /tmp/anthares-emulator.log; exit 4; }
  sleep 5
done
echo 'ANTHARES_ANDROID_BOOT=TIMEOUT'; exit 5
