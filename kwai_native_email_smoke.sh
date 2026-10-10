#!/usr/bin/env bash
# Five-minute, credential-free live probe of the Kwai native Email entry.
# No publication, login secrets, persistent session, or raw UI artifacts.
set -Eeuo pipefail
STATUS=kwai-native-email-status.txt
: > "$STATUS"
signal(){ printf '%s\n' "$1" | tee -a "$STATUS"; }
dump_ui(){
  timeout 12 adb shell uiautomator dump /sdcard/kwai-email-smoke.xml >/dev/null 2>&1 || return 1
  timeout 8 adb exec-out cat /sdcard/kwai-email-smoke.xml >/tmp/kwai-email-smoke.xml 2>/dev/null || return 1
  test -s /tmp/kwai-email-smoke.xml
}
tap_coords(){
  local coords="$1"
  [[ "$coords" =~ ^[0-9]+[[:space:]][0-9]+$ ]] || return 1
  adb shell input tap $coords >/dev/null 2>&1
}
timeout 75 adb wait-for-device
timeout 60 bash -c 'until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = "1" ]; do sleep 2; done'
bash kwai_vault_install.sh >/tmp/kwai-vault-install-smoke.log 2>&1 || {
  signal "TEST_VALIDITY=INVALID_VAULT_INSTALL"
  exit 31
}
adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS >/dev/null 2>&1 || true
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
signal "TEST_VALIDITY=KWAI_APP_LAUNCHED"
deadline=$((SECONDS+110))
while [ "$SECONDS" -lt "$deadline" ]; do
  if ! dump_ui; then sleep 2; continue; fi
  if python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-email-smoke.xml >/dev/null; then
    signal "SUCCESS_SIGNAL=KWAI_NATIVE_EMAIL_FORM_VISIBLE"
    exit 0
  fi
  if python3 tools/kwai_login_ui_locator.py native-chooser /tmp/kwai-email-smoke.xml >/dev/null; then
    signal "KWAI_NATIVE_CHOOSER_FOUND"
    coords="$(python3 tools/kwai_login_ui_locator.py email-entry /tmp/kwai-email-smoke.xml)" || {
      signal "FAILURE_SIGNAL=EMAIL_ENTRY_COORDS_NOT_FOUND"
      exit 32
    }
    tap_coords "$coords"
    signal "KWAI_NATIVE_EMAIL_TAPPED"
    sleep 3
    if dump_ui && python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-email-smoke.xml >/dev/null; then
      signal "SUCCESS_SIGNAL=KWAI_NATIVE_EMAIL_FORM_VISIBLE"
      exit 0
    fi
    signal "FAILURE_SIGNAL=EMAIL_TAP_NO_FORM"
    exit 33
  fi
  if coords="$(python3 tools/kwai_login_ui_locator.py profile-tab /tmp/kwai-email-smoke.xml 2>/dev/null)"; then
    tap_coords "$coords" || true
    signal "KWAI_PROFILE_TAB_TAPPED"
  elif grep -Eqi 'Choose like or dislike|let us know you better' /tmp/kwai-email-smoke.xml; then
    dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
    w="${dims%x*}"; h="${dims#*x}"
    if [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]]; then
      adb shell input tap $((w*75/100)) $((h*925/1000)) >/dev/null 2>&1 || true
      signal "KWAI_ONBOARDING_RIGHT_HEART"
    fi
  fi
  sleep 2
done
signal "FAILURE_SIGNAL=KWAI_NATIVE_CHOOSER_NOT_REACHED_110S"
exit 34
