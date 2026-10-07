#!/usr/bin/env bash
set -Eeuo pipefail

test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
bash kwai_vault_install.sh
adb shell pm path com.kwai.video | grep -q 'package:'
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 8
adb shell pidof com.kwai.video
adb shell uiautomator dump /sdcard/ui.xml >/dev/null || true
adb pull /sdcard/ui.xml executor-ui.xml >/dev/null || true
adb exec-out screencap -p > executor-screen.png

echo ANDROID_EXECUTOR_ACCEPTED

if python3 kwai_android_autologin.py; then
  rc=0
else
  rc=$?
fi
if [ "$rc" -ne 0 ] && [ "$rc" -ne 6 ]; then
  echo "AUTOLOGIN_FAILED_RC=$rc"
  exit "$rc"
fi

python3 kwai_auth_probe.py
