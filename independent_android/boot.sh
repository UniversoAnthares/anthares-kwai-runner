#!/usr/bin/env bash
# Anthares-owned Android emulator provisioning: no third-party workflow action.
set -Eeuo pipefail
export ANDROID_HOME="${ANDROID_HOME:-$HOME/android-sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
SDK_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
SDK_SHA256="2a7f1e7e6e6d5f8b3cf4e66a6e0a7df3c1b3c40b7e2f4d1c2a7e3e9a7c6e2f3a"
mkdir -p "$ANDROID_HOME/cmdline-tools" "$HOME/.android"
if ! command -v sdkmanager >/dev/null 2>&1; then
  echo ANTHARES_SDK_BOOTSTRAP_REQUIRED=1
  # Ubuntu GitHub-hosted images normally ship Android command-line tools.
  # Fail closed rather than download an unverified binary.
  exit 12
fi
yes | sdkmanager --licenses >/dev/null 2>&1 || true
sdkmanager --install "platform-tools" "emulator" "platforms;android-35" "system-images;android-35;google_apis;x86_64"
printf 'no\n' | avdmanager create avd -n anthares_35 -k 'system-images;android-35;google_apis;x86_64' --force
AVD_INI="$(find "$HOME/.android/avd" "$HOME/.config/.android/avd" "$ANDROID_HOME/avd" -name config.ini -path "*/anthares_35.avd/*" -print -quit 2>/dev/null || true)"
if [ -z "$AVD_INI" ]; then echo ANTHARES_AVD_CREATION_FAILED=1; avdmanager list avd || true; exit 8; fi
test -e /dev/kvm
sudo chmod 666 /dev/kvm
echo "ANTHARES_AVD_PATH=$AVD_INI"
echo "ANTHARES_EMULATOR_BINARY=$(command -v emulator)"
emulator -avd anthares_35 -no-window -no-audio -no-boot-anim -no-snapshot -accel on -no-metrics ${ANTHARES_EMU_EXTRA:--gpu swiftshader_indirect} >"$RUNNER_TEMP/anthares-emulator.log" 2>&1 &
PID=$!
trap 'adb emu kill >/dev/null 2>&1 || true; kill "$PID" >/dev/null 2>&1 || true' EXIT
timeout 150 adb wait-for-device || { echo ANTHARES_ADB_DEVICE_TIMEOUT=1; adb devices -l || true; tail -100 "$RUNNER_TEMP/anthares-emulator.log" || true; exit 6; }
for i in $(seq 1 90); do
  if [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ]; then
    echo ANTHARES_ANDROID_BOOT=PASS
    python3 independent_android/preflight.py
    bash independent_android/install_kwai.sh
    exit $?
  fi
  if ! kill -0 "$PID" 2>/dev/null; then echo ANTHARES_EMULATOR_EXITED=1; exit 4; fi
  sleep 5
done
echo ANTHARES_ANDROID_BOOT_TIMEOUT=1
exit 5
