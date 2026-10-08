#!/usr/bin/env bash
set -Eeuo pipefail
REPORT="kwai-remote-status.txt"; SHOT="kwai-remote-ready.png"; : > "$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }
capture(){ adb exec-out screencap -p > "$SHOT" 2>/dev/null || true; }
finish_diag(){ { echo "=== adb ==="; adb devices -l || true; echo "=== accounts ==="; adb shell dumpsys account 2>/dev/null | grep -E 'Account \{|type=com.google' | tail -20 || true; echo "=== package ==="; adb shell pm path com.kwai.video || true; echo "=== foreground ==="; adb shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | tail -8 || true; echo "=== activity ==="; adb shell dumpsys activity activities 2>/dev/null | grep -E 'TinyGoogleSSOActivity|SignInHubActivity|SignInActivity|TinyLoginActivity' | tail -20 || true; echo "=== tunnel ==="; tail -30 /tmp/tunnel.log 2>/dev/null || true; echo "=== ui ==="; tail -30 /tmp/android-ui.log 2>/dev/null || true; } >> "$REPORT"; capture; }
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
dismiss_notification_permission(){
  dump_ui || return 0
  grep -Eqi 'Allow Kwai to send you notifications|Don.t allow|Não permitir|Permitir notificações' /tmp/kwai-ui.xml || return 0
  local xy
  xy="$(python3 - <<'PY'
import re, xml.etree.ElementTree as ET
try:
    root=ET.parse('/tmp/kwai-ui.xml').getroot()
    for n in root.iter('node'):
        label=((n.attrib.get('text') or '')+' '+(n.attrib.get('content-desc') or '')).strip().lower()
        if 'don.t allow' in label or "don't allow" in label or 'não permitir' in label:
            m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.attrib.get('bounds',''))
            if m:
                x1,y1,x2,y2=map(int,m.groups())
                print((x1+x2)//2,(y1+y2)//2)
                break
except Exception: pass
PY
)"
  if [ -n "$xy" ]; then
    adb shell input tap $xy >/dev/null 2>&1 || true
    log "KWAI_NOTIFICATION_PERMISSION_DISMISSED"
  fi
}
dismiss_resource_overlay(){
  dump_ui || return 0
  grep -Eqi 'Resource downloading|access to all the features|resource.*download' /tmp/kwai-ui.xml || return 0
  local xy
  xy="$(python3 - <<'PY'
import re, xml.etree.ElementTree as ET
try:
    root=ET.parse('/tmp/kwai-ui.xml').getroot()
    for n in root.iter('node'):
        text=(n.attrib.get('text') or n.attrib.get('content-desc') or '').strip().lower()
        if text == 'hide':
            m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', n.attrib.get('bounds',''))
            if m:
                x1,y1,x2,y2=map(int,m.groups())
                print((x1+x2)//2, (y1+y2)//2)
                break
except Exception:
    pass
PY
)"
  if [ -n "$xy" ]; then
    adb shell input tap $xy >/dev/null 2>&1 || true
    log "KWAI_RESOURCE_DOWNLOAD_OVERLAY_DISMISSED"
  else
    adb shell input tap 540 920 >/dev/null 2>&1 || true
    log "KWAI_RESOURCE_DOWNLOAD_OVERLAY_DISMISSED_FALLBACK"
  fi
  sleep 1
  return 0
}
adb wait-for-device
for _ in $(seq 1 30); do [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = "1" ] && break; sleep 2; done
[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = "1" ] || { log "FAIL: android-not-ready"; exit 21; }
log "ANDROID_READY"
if adb shell pm path com.kwai.video 2>/dev/null | grep -q 'package:'; then
  log "KWAI_ALREADY_INSTALLED"
else
  [ -s kwai-vault/MANIFEST.tsv ] || { log "FAIL: validated-vault-missing"; exit 29; }
  bash kwai_vault_install.sh >>"$REPORT" 2>&1 || { log "FAIL: validated-vault-install"; exit 30; }
  log "KWAI_INSTALLED_FROM_VALIDATED_VAULT"
fi
launch_kwai
sleep 2
for _ in $(seq 1 8); do
  capture
  if kwai_foreground && ! google_sso_foreground; then dismiss_notification_permission; dismiss_resource_overlay; fi
  dump_ui || true
  if [ -s /tmp/kwai-ui.xml ] && grep -Eq 'text="[^"]+"|content-desc="[^"]+"' /tmp/kwai-ui.xml && ! grep -qi 'Make Everyone Shine' /tmp/kwai-ui.xml; then
    log "KWAI_UI_INTERACTIVE"; break
  fi
  sleep 2
done
if ! grep -Eq 'text="[^"]+"|content-desc="[^"]+"' /tmp/kwai-ui.xml 2>/dev/null; then
  log "FAIL: kwai-stuck-before-interactive-ui"
  adb logcat -d -t 500 2>/dev/null | grep -Ei 'AndroidRuntime|FATAL EXCEPTION|UnsatisfiedLinkError|linker|com\.kwai\.video|gifshow' | tail -120 >>"$REPORT" || true
  exit 32
fi
log "KWAI_LOGIN_UI_OPENED"
log "KWAI_OWNER_INTERACTION_READY"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  printf '\n**KWAI_OWNER_INTERACTION_READY** — use the remote URL shown above.\n' >> "$GITHUB_STEP_SUMMARY"
fi
LOGIN_DEADLINE=$((SECONDS+900))
SSO_WAS_ACTIVE=0
SSO_STARTED_AT=0
OVERLAY_LAST_CHECK=0
while [ "$SECONDS" -lt "$LOGIN_DEADLINE" ]; do
  if google_sso_foreground; then
    if [ "$SSO_WAS_ACTIVE" -eq 0 ]; then
      SSO_WAS_ACTIVE=1; SSO_STARTED_AT=$SECONDS
      log "GOOGLE_SSO_ACTIVE_DO_NOT_INTERRUPT"
    elif [ $((SECONDS-SSO_STARTED_AT)) -eq 60 ]; then
      log "GOOGLE_SSO_STILL_ACTIVE_60S_WAITING_FOR_CALLBACK"
    fi
  else
    if [ "$SSO_WAS_ACTIVE" -eq 1 ]; then
      SSO_WAS_ACTIVE=0
      if kwai_foreground; then log "GOOGLE_SSO_RETURNED_TO_KWAI"; else log "GOOGLE_SSO_LEFT_FOREGROUND"; fi
    fi
    if kwai_foreground && [ $((SECONDS-OVERLAY_LAST_CHECK)) -ge 3 ]; then
      OVERLAY_LAST_CHECK=$SECONDS
      dismiss_notification_permission
      dismiss_resource_overlay
    fi
  fi
  if [ -f /tmp/anthares-android-done ]; then
    log "DONE_SIGNAL_RECEIVED"
    dump_ui || true
    if ! python3 kwai_auth_probe.py > /tmp/kwai-auth-probe.log 2>&1 || ! grep -qx "KWAI_AUTH_STATE=AUTHENTICATED_UI" /tmp/kwai-auth-probe.log; then
      log "LOGIN_NOT_CONFIRMED_IDENTITY_UNKNOWN"; rm -f /tmp/anthares-android-done
    else
      log "KWAI_LOGIN_CONFIRMED"
      capture
      adb shell run-as com.kwai.video id >>"$REPORT" 2>&1 && log "APP_STATE_RUN_AS_AVAILABLE" || log "APP_STATE_RUN_AS_UNAVAILABLE"
      bash kwai_session_state.sh save >>"$REPORT" 2>&1 || log "KWAI_SESSION_SAVE_WARNING"
      exit 0
    fi
  fi
  kill -0 "$UI_PID" 2>/dev/null || { log "FAIL: remote-ui-died-during-login"; exit 26; }
  kill -0 "$TUNNEL_PID" 2>/dev/null || { log "FAIL: tunnel-died-during-login"; exit 27; }
  sleep 1
done
log "FAIL: login-window-expired-900s"; exit 28
