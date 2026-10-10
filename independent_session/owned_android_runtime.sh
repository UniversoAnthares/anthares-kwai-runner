#!/usr/bin/env bash
# Owned AVD bootstrap: no third-party Android runner action, no account access.
set -euo pipefail
: "${ANDROID_HOME:=${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
export ANDROID_HOME
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$PATH"
command -v sdkmanager >/dev/null || { echo 'SDKMANAGER_MISSING'; exit 2; }
command -v avdmanager >/dev/null || { echo 'AVDMANAGER_MISSING'; exit 2; }
command -v emulator >/dev/null || { echo 'EMULATOR_MISSING'; exit 2; }
if [[ ! -r /dev/kvm || ! -w /dev/kvm ]]; then echo 'KVM_UNAVAILABLE'; exit 2; fi
SDK_IMAGE="system-images;android-35;google_apis;x86_64"
sdkmanager --install 'platform-tools' 'emulator' "$SDK_IMAGE" >/dev/null
printf 'no\n' | avdmanager create avd -n anthares_owned -k "$SDK_IMAGE" -d pixel_6 --force >/dev/null
"$ANDROID_HOME/emulator/emulator" -avd anthares_owned -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect -no-snapshot-save -port 5554 >/tmp/anthares-emulator.log 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true' EXIT
adb wait-for-device
ready=0
for i in $(seq 1 120); do
  if [[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == 1 ]]; then ready=1; break; fi
  sleep 2
done
[[ "$ready" == 1 ]] || { echo 'ANDROID_BOOT_TIMEOUT'; exit 1; }
adb shell getprop ro.build.version.sdk | grep -qx '35'
echo 'OWN_ANDROID_RUNTIME_BOOT_VERIFIED'
# No account session or snapshot leaves this runner in the smoke test.
