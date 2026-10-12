#!/usr/bin/env bash
set -Eeuo pipefail
MODE="${1:-deeplink-login}"
SETTLE="${2:-5}"
REPORT=kwai-direct-auth-probe.txt
: > "$REPORT"
log(){ echo "$*" | tee -a "$REPORT"; }

bash kwai_vault_install.sh
adb shell svc wifi enable >/dev/null 2>&1 || true
adb shell svc data enable >/dev/null 2>&1 || true
adb shell settings put global captive_portal_mode 0 >/dev/null 2>&1 || true
sleep 2

adb shell dumpsys package com.kwai.video > kwai-package-dump.txt || true
grep -Eo 'com\.kwai\.video/[A-Za-z0-9_.$]+' kwai-package-dump.txt | sort -u > kwai-components.txt || true
grep -Ei 'login|signin|sign_in|auth|account|phone|email' kwai-components.txt > kwai-auth-components.txt || true
log "MODE=$MODE SETTLE=$SETTLE"
log "AUTH_COMPONENT_COUNT=$(wc -l < kwai-auth-components.txt | tr -d ' ')"

start_uri(){
  local uri="$1"
  log "START_URI=$uri"
  adb shell am start -W -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "$uri" -p com.kwai.video >>"$REPORT" 2>&1 || true
}
start_component(){
  local pattern="$1"
  local comp
  comp="$(grep -Ei "$pattern" kwai-auth-components.txt | head -1 || true)"
  if [ -z "$comp" ]; then
    log "NO_COMPONENT_FOR=$pattern"
    return 0
  fi
  log "START_COMPONENT=$comp"
  adb shell am start -W -n "$comp" >>"$REPORT" 2>&1 || true
}

case "$MODE" in
  deeplink-login) start_uri 'kwai://login' ;;
  deeplink-signin) start_uri 'kwai://signin' ;;
  deeplink-account) start_uri 'kwai://account/login' ;;
  deeplink-profile) start_uri 'kwai://profile' ;;
  component-login) start_component 'login|signin|sign_in' ;;
  component-auth) start_component 'auth' ;;
  component-account) start_component 'account|phone|email' ;;
  profile-deny-permission)
    adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
    sleep 4
    # Use the known bottom-profile area only in this fallback strategy.
    adb shell input tap 960 2200 || true
    sleep 2
    ;;
  *) log "UNKNOWN_MODE=$MODE"; exit 2 ;;
esac

sleep "$SETTLE"

# If Android permission controller blocks the app, choose the explicit Deny button.
# This avoids granting contacts/location/media permissions that are not required for login.
for i in 1 2; do
  adb shell uiautomator dump /sdcard/direct-auth.xml >/dev/null 2>&1 || true
  adb exec-out cat /sdcard/direct-auth.xml > direct-auth.xml 2>/dev/null || true
  if grep -q 'permission_deny_button' direct-auth.xml 2>/dev/null; then
    python3 - <<'PY'
import re,subprocess,xml.etree.ElementTree as ET
p='direct-auth.xml'
try:r=ET.parse(p).getroot()
except Exception:raise SystemExit(0)
for n in r.iter('node'):
    if (n.get('resource-id') or '').endswith('/permission_deny_button'):
        m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds') or '')
        if m:
            a,b,c,d=map(int,m.groups())
            subprocess.run(['adb','shell','input','tap',str((a+c)//2),str((b+d)//2)],check=False)
            break
PY
    log PERMISSION_DIALOG_DENIED=1
    sleep 4
  else
    break
  fi
done

# Recover from SetupWizard stealing foreground without interacting with account/security UI.
FOCUS="$(adb shell dumpsys window windows 2>/dev/null | grep -m1 'mCurrentFocus' || true)"
if echo "$FOCUS" | grep -q 'com.google.android.setupwizard'; then
  log SETUPWIZARD_STOLE_FOREGROUND=1
  adb shell input keyevent KEYCODE_HOME || true
  sleep 1
  adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
  sleep 5
fi

# Validate only the login surface; do not dump credential values.
for attempt in 1 2 3 4; do
  adb shell uiautomator dump /sdcard/direct-auth.xml >/dev/null 2>&1 || true
  adb exec-out cat /sdcard/direct-auth.xml > direct-auth.xml 2>/dev/null || true
  if python3 tools/kwai_login_ui_locator.py native-chooser direct-auth.xml >/dev/null 2>&1; then
    log "KWAI_DIRECT_AUTH_SURFACE=CHOOSER ATTEMPT=$attempt"
    exit 0
  fi
  if python3 tools/kwai_login_ui_locator.py email-form direct-auth.xml >/dev/null 2>&1; then
    log "KWAI_DIRECT_AUTH_SURFACE=FORM ATTEMPT=$attempt"
    exit 0
  fi
  sleep 3
done

adb shell dumpsys activity activities > kwai-direct-activities.txt || true
adb shell dumpsys window windows > kwai-direct-window.txt || true
adb logcat -d -v brief | grep -Ei 'com.kwai.video|AndroidRuntime|FATAL EXCEPTION|SIGSEGV|UnsatisfiedLinkError|Permission Denial|ActivityNotFound|not exported|ANR' | tail -160 > kwai-direct-logcat.txt || true
PID="$(adb shell pidof com.kwai.video 2>/dev/null | tr -d '\r' || true)"
log "KWAI_PID=${PID:-none}"
log "KWAI_DIRECT_AUTH_SURFACE=NOT_REACHED"
exit 31
