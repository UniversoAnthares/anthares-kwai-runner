#!/usr/bin/env bash
set -euo pipefail
mkdir -p /tmp/anthares-stage3
adb wait-for-device
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1
adb shell am start -a android.intent.action.MAIN -c android.intent.category.HOME | tee /tmp/anthares-stage3/launch.log
adb shell pm list packages > /tmp/anthares-stage3/packages.txt
adb shell dumpsys activity activities > /tmp/anthares-stage3/activities.txt
adb shell screencap -p /sdcard/anthares-stage3.png
adb pull /sdcard/anthares-stage3.png /tmp/anthares-stage3/screenshot.png
test -s /tmp/anthares-stage3/screenshot.png
if [[ -n "${ANDROID_TEST_APK:-}" ]]; then
  test -f "$ANDROID_TEST_APK"
  adb install -r "$ANDROID_TEST_APK" | tee /tmp/anthares-stage3/install.log
  if [[ -n "${ANDROID_TEST_PACKAGE:-}" ]]; then
    adb shell monkey -p "$ANDROID_TEST_PACKAGE" -c android.intent.category.LAUNCHER 1 | tee /tmp/anthares-stage3/app-launch.log
    adb shell pidof "$ANDROID_TEST_PACKAGE" | tee /tmp/anthares-stage3/app-pid.log
  fi
fi
echo ANDROID_STAGE3_READY
