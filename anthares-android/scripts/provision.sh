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
printf 'no\n' | avdmanager create avd --force -n anthares_android -k 'system-images;android-35;google_apis;x86_64' --device pixel_5
emulator -avd anthares_android -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader_indirect -accel on > /tmp/anthares-emulator.log 2>&1 &
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
