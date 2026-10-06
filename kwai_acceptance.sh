#!/usr/bin/env bash
set -Eeuo pipefail

test "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1"
bash kwai_vault_install.sh
adb shell pm path com.kwai.video | grep -q 'package:'
adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS >/dev/null 2>&1 || true
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 8
adb shell pidof com.kwai.video
adb shell uiautomator dump /sdcard/ui.xml >/dev/null || true
adb pull /sdcard/ui.xml executor-ui.xml >/dev/null || true
adb exec-out screencap -p > executor-screen.png || true
echo ANDROID_EXECUTOR_ACCEPTED

# Normalize launcher/onboarding through the proven state-driven recovery before credentials.
python3 kwai_state_driver.py | tee /tmp/kwai-fsm.log
grep -q FSM_MAIN_REACHED /tmp/kwai-fsm.log
echo TEST_VALIDITY=FSM_MAIN_REACHED

set +e
python3 kwai_android_autologin.py
rc=$?
set -e
case "$rc" in
  0|6) ;;
  *) echo "AUTOLOGIN_FAILED_RC=$rc"; exit "$rc" ;;
esac
python3 kwai_auth_probe.py
