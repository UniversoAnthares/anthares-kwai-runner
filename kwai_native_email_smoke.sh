#!/usr/bin/env bash
# Bounded remote Android diagnosis. No credentials, private UI text, screenshots or publication.
set -Eeuo pipefail
STATUS=kwai-native-email-status.txt
: > "$STATUS"
causal_probe(){
  local report
  report="$(python3 tools/kwai_android_causal_probe.py 2>/dev/null)" || return 0
  # JSON contains only counts and boolean health flags.
  signal "ANDROID_CAUSAL=$report"
}
environment_probe(){
  local report
  report="$(python3 tools/kwai_android_environment_probe.py 2>/dev/null)" || return 0
  signal "ANDROID_ENVIRONMENT=$report"
}
trap 'causal_probe; environment_probe' EXIT
signal(){ printf '%s\n' "$1" | tee -a "$STATUS"; }
dump_ui(){
  timeout 8 adb shell uiautomator dump /sdcard/kwai-email-smoke.xml >/dev/null 2>&1 || return 1
  timeout 5 adb exec-out cat /sdcard/kwai-email-smoke.xml >/tmp/kwai-email-smoke.xml 2>/dev/null || return 1
  test -s /tmp/kwai-email-smoke.xml
}
tap_coords(){
  local coords="$1"
  [[ "$coords" =~ ^[0-9]+[[:space:]][0-9]+$ ]] || return 1
  adb shell input tap $coords >/dev/null 2>&1
}
state_flag(){
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("1" if d.get(sys.argv[2]) else "0")' "$1" "$2"
}
focus_package(){
  local focus
  focus="$(timeout 4 adb shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | tail -1 || true)"
  if [[ "$focus" == *com.kwai.video* ]]; then echo kwai
  elif [[ "$focus" == *com.android.permissioncontroller* ]]; then echo permission
  elif [[ "$focus" == *com.google.android* ]]; then echo google
  elif [[ -z "$focus" ]]; then echo unknown
  else echo other; fi
}
tap_onboarding(){
  local dims w h
  dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  w="${dims%x*}"; h="${dims#*x}"
  [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 1
  adb shell input tap $((w*75/100)) $((h*94/100)) >/dev/null 2>&1
}
timeout 60 adb wait-for-device
timeout 55 bash -c 'until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = "1" ]; do sleep 2; done'
bash kwai_vault_install.sh >/tmp/kwai-vault-install-smoke.log 2>&1 || {
  signal "TEST_VALIDITY=INVALID_VAULT_INSTALL"
  exit 31
}
adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS >/dev/null 2>&1 || true
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
signal "TEST_VALIDITY=KWAI_APP_LAUNCHED"
python3 tools/kwai_android_startup_fingerprint.py || true
deadline=$((SECONDS+95))
previous=""
onboarding_taps=0
profile_taps=0
valid_dumps=0
invalid_dumps=0
app_error_restarts=0
profile_route_fallbacks=0
stagnant_dumps=0
while [ "$SECONDS" -lt "$deadline" ]; do
  if ! dump_ui; then
    invalid_dumps=$((invalid_dumps+1))
    sleep 1
    continue
  fi
  valid_dumps=$((valid_dumps+1))
  state="$(python3 tools/kwai_ui_safe_diagnose.py /tmp/kwai-email-smoke.xml)" || {
    invalid_dumps=$((invalid_dumps+1))
    sleep 1
    continue
  }
  # State data is restricted to boolean allowlisted UI signals and node counts.
  signature="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(",".join(k for k,v in d.items() if v is True))' "$state")"
  if [ "$signature" != "$previous" ]; then
    signal "UI_STATE=${signature:-unclassified};FOCUS=$(focus_package)"
    signal "PROFILE_CANDIDATES=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("exact=%s,bottom=%s,idhint=%s"%(d.get("profile_exact_label_count",0),d.get("profile_bottom_label_count",0),d.get("profile_resource_hint_count",0)))' "$state")"
    signal "AUTH_ROUTES=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("phone=%d,google=%d,email=%d,otp=%d,captcha=%d"%tuple(int(bool(d.get(k))) for k in ("phone_login_option","google_login_option","email_login_option","verification_challenge","captcha_challenge")))' "$state")"
    signal "PROFILE_GEOMETRY=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("bounded=%s,bottom=%s,unbounded=%s,height=%s"%(d.get("profile_hint_bounded_count",0),d.get("profile_hint_bottom_count",0),d.get("profile_hint_unbounded_count",0),d.get("screen_height_bucket","unknown")))' "$state")"
    previous="$signature"
    stagnant_dumps=0
  else
    stagnant_dumps=$((stagnant_dumps+1))
  fi
  if python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-email-smoke.xml >/dev/null; then
    signal "SUCCESS_SIGNAL=KWAI_NATIVE_EMAIL_FORM_VISIBLE"
    exit 0
  fi
  if python3 tools/kwai_login_ui_locator.py native-chooser /tmp/kwai-email-smoke.xml >/dev/null; then
    signal "KWAI_NATIVE_CHOOSER_FOUND"
    coords="$(python3 tools/kwai_login_ui_locator.py email-entry /tmp/kwai-email-smoke.xml)" || {
      signal "FAILURE_SIGNAL=EMAIL_ENTRY_COORDS_NOT_FOUND"; exit 32;
    }
    tap_coords "$coords"
    signal "KWAI_NATIVE_EMAIL_TAPPED"
    sleep 2
    if dump_ui && python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-email-smoke.xml >/dev/null; then
      signal "SUCCESS_SIGNAL=KWAI_NATIVE_EMAIL_FORM_VISIBLE"; exit 0
    fi
    signal "FAILURE_SIGNAL=EMAIL_TAP_NO_FORM"; exit 33
  fi
  if [ "$(state_flag "$state" verification_challenge)" = 1 ]; then
    signal "BLOCKER=ACCOUNT_OTP_VERIFICATION_REQUIRED"
    exit 36
  fi
  if [ "$(state_flag "$state" captcha_challenge)" = 1 ]; then
    signal "BLOCKER=ACCOUNT_CAPTCHA_VERIFICATION_REQUIRED"
    exit 37
  fi
  if [ "$(state_flag "$state" permission_modal)" = 1 ]; then
    signal "BLOCKER=ANDROID_PERMISSION_MODAL"
    break
  fi
  if [ "$(state_flag "$state" resource_overlay)" = 1 ]; then
    signal "BLOCKER=KWAI_RESOURCE_OVERLAY"
    break
  fi
  if [ "$(state_flag "$state" system_error_unattributed)" = 1 ]; then
    signal "ANDROID_ERROR_ATTRIBUTION=UNCONFIRMED"
  fi
  if [ "$(state_flag "$state" system_error)" = 1 ]; then
    if [ "$app_error_restarts" -lt 1 ]; then
      app_error_restarts=$((app_error_restarts+1))
      signal "RECOVERY=BOUNDED_APP_RELAUNCH"
      adb shell am force-stop com.kwai.video >/dev/null 2>&1 || true
      adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
      sleep 4
      continue
    fi
    python3 tools/kwai_android_startup_fingerprint.py || true
    signal "BLOCKER=ANDROID_APP_ERROR_AFTER_RELAUNCH"
    break
  fi
  if [ "$(state_flag "$state" interest_onboarding)" = 1 ]; then
    if [ "$onboarding_taps" -ge 12 ]; then
      signal "BLOCKER=ONBOARDING_NOT_ADVANCING_AFTER_12_TAPS"
      break
    fi
    tap_onboarding || { signal "BLOCKER=UNKNOWN_SCREEN_SIZE"; break; }
    onboarding_taps=$((onboarding_taps+1))
    signal "KWAI_ONBOARDING_TAP_COUNT=$onboarding_taps"
    sleep 2
    continue
  fi
  # The semantic locator, not a broad classifier flag, decides tap safety.
  if [ "$profile_taps" -lt 2 ]; then
    coords="$(python3 tools/kwai_login_ui_locator.py profile-tab /tmp/kwai-email-smoke.xml 2>/dev/null)" || coords=""
    if [ -n "$coords" ]; then
      tap_coords "$coords" || true
      profile_taps=$((profile_taps+1))
      signal "KWAI_PROFILE_TAP_COUNT=$profile_taps"
      sleep 2
      continue
    fi
  fi
  # If the app is on the main feed but no semantic profile node is
  # actionable, try exactly one geometry-based bottom-right tab tap.
  # The action is constrained to the nav band and is never repeated blindly.
  if [ "$(state_flag "$state" main_navigation)" = 1 ] &&
     [ "$(state_flag "$state" profile_tab)" != 1 ] &&
     [ "$profile_route_fallbacks" -lt 1 ] && [ "$stagnant_dumps" -ge 3 ]; then
    dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1 || true)"
    if [[ "$dims" =~ ^[0-9]+x[0-9]+$ ]]; then
      w="${dims%x*}"; h="${dims#*x}"
      adb shell input tap $((w*90/100)) $((h*95/100)) >/dev/null 2>&1 || true
      profile_route_fallbacks=$((profile_route_fallbacks+1))
      signal "RECOVERY=BOUNDED_BOTTOM_RIGHT_PROFILE_TAB"
      sleep 3
      continue
    fi
  fi
  sleep 2
done
# Final bounded recovery uses the observed native platform widget and no secrets.
if timeout 40 python3 tools/kwai_login_surface_recovery.py >/tmp/kwai-safe-recovery.log 2>&1; then
  signal "RECOVERY=KWAI_NATIVE_LOGIN_SURFACE_REACHED"
  if dump_ui && python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-email-smoke.xml >/dev/null; then
    signal "SUCCESS_SIGNAL=KWAI_NATIVE_EMAIL_FORM_VISIBLE"
    exit 0
  fi
  if dump_ui && python3 tools/kwai_login_ui_locator.py native-chooser /tmp/kwai-email-smoke.xml >/dev/null; then
    coords="$(python3 tools/kwai_login_ui_locator.py email-entry /tmp/kwai-email-smoke.xml)" || coords=""
    if [ -n "$coords" ]; then
      tap_coords "$coords" || true
      sleep 2
      if dump_ui && python3 tools/kwai_login_ui_locator.py email-form /tmp/kwai-email-smoke.xml >/dev/null; then
        signal "SUCCESS_SIGNAL=KWAI_NATIVE_EMAIL_FORM_VISIBLE"
        exit 0
      fi
    fi
  fi
fi
signal "UI_DUMPS_VALID=$valid_dumps;INVALID=$invalid_dumps;ONBOARDING_TAPS=$onboarding_taps;PROFILE_TAPS=$profile_taps"
signal "FAILURE_SIGNAL=KWAI_NATIVE_CHOOSER_NOT_REACHED_DIAGNOSED"
exit 34
