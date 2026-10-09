#!/usr/bin/env bash
set -Eeuo pipefail
REPORT="kwai-remote-status.txt"; SHOT="kwai-remote-ready.png"; : > "$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }
capture(){ adb exec-out screencap -p > "$SHOT" 2>/dev/null || true; }
finish_diag(){ { echo "=== adb ==="; adb devices -l || true; echo "=== accounts ==="; adb shell dumpsys account 2>/dev/null | grep -E 'Account \{|type=com.google' | tail -20 || true; echo "=== package ==="; adb shell pm path com.kwai.video || true; echo "=== foreground ==="; adb shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | tail -8 || true; echo "=== activity ==="; adb shell dumpsys activity activities 2>/dev/null | grep -E 'TinyGoogleSSOActivity|SignInHubActivity|SignInActivity' | tail -20 || true; echo "=== tunnel ==="; tail -30 /tmp/tunnel.log 2>/dev/null || true; echo "=== ui ==="; tail -30 /tmp/android-ui.log 2>/dev/null || true; } >> "$REPORT"; capture; }
cleanup(){ finish_diag; [ -n "${UI_PID:-}" ] && kill "$UI_PID" 2>/dev/null || true; [ -n "${TUNNEL_PID:-}" ] && kill "$TUNNEL_PID" 2>/dev/null || true; }
trap cleanup EXIT
launch_kwai(){
  local c
  c="$(adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.kwai.video 2>/dev/null | tr -d '\r' | tail -1)"
  if [ -n "$c" ] && [[ "$c" == com.kwai.video/* ]]; then
    adb shell am start -n "$c" >/dev/null 2>&1 || true
  else
    adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
  fi
}
current_focus(){ adb shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | tail -2 | tr '\n' ' '; }
google_sso_foreground(){ current_focus | grep -Eq 'com\.google\.android\.gms|TinyGoogleSSOActivity|SignInHubActivity|SignInActivity'; }
kwai_foreground(){ current_focus | grep -q 'com\.kwai\.video'; }
dump_ui(){
  adb shell uiautomator dump /sdcard/kwai-ui.xml >/dev/null 2>&1 || return 1
  adb pull /sdcard/kwai-ui.xml /tmp/kwai-ui.xml >/dev/null 2>&1 || return 1
  [ -s /tmp/kwai-ui.xml ]
}
tap_label(){
  local pat="$1" xy
  dump_ui || return 1
  xy="$(PAT="$pat" python3 - <<'PY'
import os,re,xml.etree.ElementTree as ET
pat=re.compile(os.environ['PAT'],re.I)
try: root=ET.parse('/tmp/kwai-ui.xml').getroot()
except Exception: raise SystemExit(1)
for n in root.iter('node'):
 s=((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip()
 if not pat.search(s): continue
 m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
 if m:
  a,b,c,d=map(int,m.groups()); print((a+c)//2,(b+d)//2); break
PY
)"
  [ -n "$xy" ] || return 1
  adb shell input tap $xy >/dev/null 2>&1
}

google_bottom_right_tap(){
  local dims w h
  dims="$(adb shell wm size 2>/dev/null | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  w="${dims%x*}"; h="${dims#*x}"
  [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 1
  adb shell input tap $((w*84/100)) $((h*95/100)) >/dev/null 2>&1
}

auto_advance_google_setup(){
  dump_ui || return 0

  if grep -Eqi 'Google Terms of Service|Google Play Terms of Service|Google Privacy Policy|Welcome|Bem-vindo' /tmp/kwai-ui.xml 2>/dev/null; then
    if tap_label '^(I agree|Concordo)$'; then
      log "GOOGLE_WELCOME_AGREEMENT_BUTTON_TAPPED"
      sleep 2
      return 0
    fi
    google_bottom_right_tap || true
    log "GOOGLE_WELCOME_AGREEMENT_FALLBACK_TAPPED"
    sleep 2
    return 0
  fi

  if grep -Eqi 'Google services|Serviços do Google' /tmp/kwai-ui.xml 2>/dev/null; then
    if tap_label '^(MORE|Mais)$'; then
      log "GOOGLE_SERVICES_MORE_TAPPED"
      sleep 2
      return 0
    fi
    if tap_label '^(ACCEPT|Aceitar)$'; then
      log "GOOGLE_SERVICES_ACCEPT_TAPPED"
      sleep 2
      return 0
    fi
    # These two controls occupy the same lower-right position on the Google
    # services flow; after MORE the same coordinate becomes ACCEPT.
    google_bottom_right_tap || true
    log "GOOGLE_SERVICES_BOTTOM_RIGHT_FALLBACK_TAPPED"
    sleep 2
    return 0
  fi
}

dismiss_notification_permission(){
  local xy
  for attempt in 1 2 3; do
    dump_ui || { sleep 1; continue; }
    xy="$(python3 - <<'PY'
import re,xml.etree.ElementTree as ET
try:
 root=ET.parse('/tmp/kwai-ui.xml').getroot()
 for n in root.iter('node'):
  label=((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().lower()
  rid=(n.get('resource-id') or '').lower()
  if ("don't allow" in label or "don’t allow" in label or "não permitir" in label or "not now" in label or "permission_deny_button" in rid):
   m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
   if m:
    a,b,c,d=map(int,m.groups());print((a+c)//2,(b+d)//2);break
except Exception:pass
PY
)"
    if [ -n "$xy" ]; then
      adb shell input tap $xy >/dev/null 2>&1 || true
      log "KWAI_NOTIFICATION_PERMISSION_DISMISSED"
      sleep 1
      return 0
    fi
    return 0
  done
}

# Preserve the remainder of the existing login automation from repository by sourcing
# the generated runtime logic below.
if [ -f /tmp/kwai_remote_android_login.runtime.original.sh ]; then
  source /tmp/kwai_remote_android_login.runtime.original.sh
  exit $?
fi

# Minimal self-contained continuation used in repository runs.
launch_kwai
LOGIN_DEADLINE=$((SECONDS+2700))
SSO_WAS_ACTIVE=0
GOOGLE_AGREEMENT_LAST_CHECK=0
log "KWAI_LOGIN_UI_OPENED"
log "KWAI_OWNER_INTERACTION_READY"
while [ "$SECONDS" -lt "$LOGIN_DEADLINE" ]; do
  if google_sso_foreground; then
    if [ $((SECONDS-GOOGLE_AGREEMENT_LAST_CHECK)) -ge 2 ]; then
      GOOGLE_AGREEMENT_LAST_CHECK=$SECONDS
      auto_advance_google_setup || true
    fi
    if [ "$SSO_WAS_ACTIVE" -eq 0 ]; then
      SSO_WAS_ACTIVE=1
      log "GOOGLE_SSO_ACTIVE_DO_NOT_INTERRUPT"
    fi
  else
    if [ "$SSO_WAS_ACTIVE" -eq 1 ]; then
      SSO_WAS_ACTIVE=0
      if kwai_foreground; then log "GOOGLE_SSO_RETURNED_TO_KWAI"; else log "GOOGLE_SSO_LEFT_FOREGROUND"; fi
    fi
  fi
  if [ -f /tmp/anthares-android-done ]; then
    log "DONE_SIGNAL_RECEIVED"
    if python3 kwai_auth_probe.py > /tmp/kwai-auth-probe.log 2>&1 && grep -qx "KWAI_AUTH_STATE=AUTHENTICATED_UI" /tmp/kwai-auth-probe.log; then
      log "KWAI_LOGIN_CONFIRMED"
      bash kwai_session_state.sh save >>"$REPORT" 2>&1 || log "KWAI_SESSION_SAVE_WARNING"
      exit 0
    fi
    rm -f /tmp/anthares-android-done
  fi
  sleep 1
done
log "FAIL: login-window-expired-2700s"
exit 28
