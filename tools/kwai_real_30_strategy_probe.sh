#!/usr/bin/env bash
# Thirty distinct real Android startup/identity-entry probes. Never reads secrets.
set -Eeuo pipefail
variant="${1:?strategy required}"
[[ "$variant" =~ ^([0-9]|10)$ ]] || exit 2
adb wait-for-device
timeout 55 bash -c 'until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = 1 ]; do sleep 2; done'
bash kwai_vault_install.sh >/tmp/kwai-30-install.log 2>&1 || { echo "RESULT=APK_INSTALL_FAILED"; exit 41; }
pkg=com.kwai.video
adb shell am force-stop "$pkg" >/dev/null 2>&1 || true
case "$variant" in
  0) adb shell monkey -p "$pkg" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 ;;
  1) adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$pkg" >/dev/null 2>&1 ;;
  2) adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$pkg" >/dev/null 2>&1; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  3) adb shell am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$pkg" >/dev/null 2>&1 ;;
  4) adb shell monkey -p "$pkg" 1 >/dev/null 2>&1; sleep 3; adb shell input keyevent KEYCODE_HOME >/dev/null 2>&1; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  5) adb shell monkey -p "$pkg" 1 >/dev/null 2>&1; sleep 3; adb shell am force-stop "$pkg"; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  6) adb shell settings put global window_animation_scale 0; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  7) adb shell settings put global animator_duration_scale 0; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  8) adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$pkg" >/dev/null 2>&1; adb shell input keyevent KEYCODE_BACK >/dev/null 2>&1; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  9) adb shell monkey -p "$pkg" 1 >/dev/null 2>&1; sleep 3; adb shell input keyevent KEYCODE_APP_SWITCH >/dev/null 2>&1; adb shell monkey -p "$pkg" 1 >/dev/null 2>&1 ;;
  10) adb shell monkey -p "$pkg" 1 >/dev/null 2>&1; sleep 3; adb shell input keyevent KEYCODE_HOME >/dev/null 2>&1; adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$pkg" >/dev/null 2>&1 ;;
esac
sleep 6
python3 tools/kwai_android_startup_fingerprint.py
python3 tools/kwai_android_causal_probe.py
if timeout 10 adb shell uiautomator dump /sdcard/kwai-30.xml >/dev/null 2>&1 && timeout 6 adb exec-out cat /sdcard/kwai-30.xml >/tmp/kwai-30.xml 2>/dev/null; then
  python3 tools/kwai_ui_safe_diagnose.py /tmp/kwai-30.xml
  if python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-30.xml >/dev/null 2>&1; then
    echo "RESULT=EMAIL_FORM_VISIBLE"
  elif python3 tools/kwai_login_ui_locator.py native-chooser /tmp/kwai-30.xml >/dev/null 2>&1; then
    echo "RESULT=LOGIN_CHOOSER_VISIBLE"
  elif python3 tools/kwai_login_ui_locator.py profile-tab /tmp/kwai-30.xml >/dev/null 2>&1; then
    echo "RESULT=PROFILE_TAB_ACTIONABLE"
    coords="$(python3 tools/kwai_login_ui_locator.py profile-tab /tmp/kwai-30.xml 2>/dev/null)" || coords=""
    if [[ "$coords" =~ ^[0-9]+[[:space:]][0-9]+$ ]]; then
      adb shell input tap $coords >/dev/null 2>&1 || true
      sleep 4
      if timeout 9 adb shell uiautomator dump /sdcard/kwai-30-after.xml >/dev/null 2>&1 && timeout 6 adb exec-out cat /sdcard/kwai-30-after.xml >/tmp/kwai-30-after.xml 2>/dev/null; then
        python3 tools/kwai_ui_safe_diagnose.py /tmp/kwai-30-after.xml
        if python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-30-after.xml >/dev/null 2>&1; then
          echo "RESULT_AFTER_TAP=EMAIL_FORM_VISIBLE"
        elif python3 tools/kwai_login_ui_locator.py native-chooser /tmp/kwai-30-after.xml >/dev/null 2>&1; then
          echo "RESULT_AFTER_TAP=NATIVE_CHOOSER_VISIBLE"
        else
          echo "RESULT_AFTER_TAP=PROFILE_TAPPED_CHOOSER_NOT_YET_VISIBLE"
        fi
      else
        echo "RESULT_AFTER_TAP=UI_DUMP_UNAVAILABLE"
      fi
    fi
  else
    echo "RESULT=NO_LOGIN_ENTRY_VISIBLE"
  fi
else
  echo "RESULT=UI_DUMP_UNAVAILABLE"
fi
