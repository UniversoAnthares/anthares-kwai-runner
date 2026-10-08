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
  # Android runtime permission is a system modal; clear it before onboarding.
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
    # If XML only exposes the modal heading, choose the lower denial button
    # using device-relative coordinates, not the browser screenshot coordinates.
    if grep -Eqi 'Allow Kwai to send you notifications|send you notifications|enviar notificações' /tmp/kwai-ui.xml; then
      local dims w h
      dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
      w="${dims%x*}"; h="${dims#*x}"
      if [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]]; then
        adb shell input tap $((w*50/100)) $((h*62/100)) >/dev/null 2>&1 || true
        log "KWAI_NOTIFICATION_PERMISSION_DISMISSED_FALLBACK"
        sleep 1
        return 0
      fi
    fi
    return 0
  done
}

complete_kwai_interest_onboarding(){
  # Kwai's 12-step like/dislike introduction must be completed before Profile.
  # Read each step from the live UI; never tap blindly outside this screen.
  local step xy previous="" attempts=0
  for attempts in $(seq 1 18); do
    dump_ui || { sleep 1; continue; }
    step="$(python3 - <<'PY'
import re,xml.etree.ElementTree as ET
try:
 root=ET.parse('/tmp/kwai-ui.xml').getroot()
 txt=' '.join((n.get('text','')+' '+n.get('content-desc','')) for n in root.iter('node'))
 if re.search(r'choose like or dislike to\\s*let us know you better',txt,re.I):
  m=re.search(r'\\b(1[0-2]|[1-9])\\s*/\\s*12\\b',txt)
  if m: print(m.group(1))
except Exception: pass
PY
)"
    [ -n "$step" ] || return 0
    xy="$(python3 - <<'PY'
import re,xml.etree.ElementTree as ET
try:
 root=ET.parse('/tmp/kwai-ui.xml').getroot()
 nodes=list(root.iter('node'))
 # Prefer the actual left (like) action if accessibility exposes its bounds.
 for n in nodes:
  t=(n.get('text','')+' '+n.get('content-desc','')).lower()
  if ('like' in t or 'curtir' in t) and 'dislike' not in t and 'choose' not in t:
   m=re.match(r'\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]',n.get('bounds',''))
   if m:
    a,b,c,d=map(int,m.groups())
    if c>a and d>b and b>400:print((a+c)//2,(b+d)//2);break
except Exception: pass
PY
)"
    if [ -z "$xy" ]; then
      local dims w h
      dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
      w="${dims%x*}"; h="${dims#*x}"
      [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 1
      xy="$((w*25/100)) $((h*97/100))"
    fi
    adb shell input tap $xy >/dev/null 2>&1 || return 1
    log "KWAI_ONBOARDING_INTEREST_STEP=${step}/12"
    sleep 2
  done
  log "KWAI_ONBOARDING_INTEREST_MAX_ATTEMPTS"
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
# Resolve the Android 13+ notification permission before the first Kwai frame.
# The permission dialog blocks onboarding and makes browser taps unreliable.
if adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS >/dev/null 2>&1; then
  log "KWAI_NOTIFICATION_PERMISSION_PREGRANTED"
else
  log "KWAI_NOTIFICATION_PERMISSION_PREGRANT_UNAVAILABLE"
fi
launch_kwai
sleep 2
for _ in $(seq 1 8); do
  capture
  if kwai_foreground && ! google_sso_foreground; then dismiss_notification_permission; complete_kwai_interest_onboarding; dismiss_resource_overlay; fi
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
# Navigate to Kwai's email login; do not mistake the feed for a login screen.
email_login_visible(){
  dump_ui || return 1
  python3 - <<'PY'
import xml.etree.ElementTree as ET
root=ET.parse('/tmp/kwai-ui.xml').getroot()
s=' '.join(((n.get('text') or '')+' '+(n.get('content-desc') or '')) for n in root.iter('node')).lower()
email=('email' in s or 'e-mail' in s or 'e‑mail' in s or 'correio eletrônico' in s)
entry=('password' in s or 'senha' in s or 'verification code' in s or 'código' in s or 'send code' in s or 'continue' in s or 'continuar' in s)
google=('accounts.google.com' in s or 'google sign in' in s)
raise SystemExit(0 if email and entry and not google else 1)
PY
}
tap_label(){
  local pattern="$1" coords
  dump_ui || return 1
  coords="$(LABEL_PATTERN="$pattern" python3 - <<'PY'
import os,re,xml.etree.ElementTree as ET
p=re.compile(os.environ['LABEL_PATTERN'],re.I)
try:
 root=ET.parse('/tmp/kwai-ui.xml').getroot()
 for n in root.iter('node'):
  t=(n.get('text') or '')+' '+(n.get('content-desc') or '')
  if p.search(t):
   m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
   if m:
    a,b,c,d=map(int,m.groups())
    if c>a and d>b:
     print((a+c)//2,(b+d)//2);break
except Exception: pass
PY
)"
  [ -n "$coords" ] || return 1
  adb shell input tap $coords >/dev/null 2>&1
  sleep 2
}
if ! email_login_visible; then
  complete_kwai_interest_onboarding || true
  log "KWAI_EMAIL_LOGIN_NAVIGATION_STARTED"
  variant=${KWAI_VARIANT:-1}
  screen="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  width="${screen%x*}"; height="${screen#*x}"
  [[ "$width" =~ ^[0-9]+$ ]] || width=1080
  [[ "$height" =~ ^[0-9]+$ ]] || height=1920
  log "KWAI_NAV_VARIANT=$variant"
  case "$variant" in
    1) tap_label '^(Profile|Perfil|Eu|Me)$' || true ;;
    2) adb shell input tap $((width*91/100)) $((height*93/100)) || true ;;
    3) adb shell input keyevent KEYCODE_BACK || true; sleep 2; tap_label '(Profile|Perfil|Me)' || true ;;
    4) adb shell am force-stop com.kwai.video || true; adb shell monkey -p com.kwai.video 1 >/dev/null 2>&1 || true; sleep 4; tap_label '(Profile|Perfil|Me)' || true ;;
    5) adb shell input tap $((width*94/100)) $((height*91/100)) || true; sleep 3; tap_label '(Log in|Sign in|Entrar|Login)' || true ;;
    *) tap_label '(Profile|Perfil|Me)' || true ;;
  esac
  sleep 2
  for _ in $(seq 1 5); do
    email_login_visible && break
    if google_sso_foreground; then log "FAILURE_SIGNAL=UNEXPECTED_GOOGLE_SSO"; exit 34; fi
    tap_label '(log[ -]?in|sign[ -]?in|entrar|fazer login|cadastre-se|sign up|register)' || true
    email_login_visible && break
    tap_label '(other methods|other ways|more options|outras opções|outras formas|use another method)' || true
    email_login_visible && break
    tap_label '(e-?mail|email address|endereço de e-mail|continuar com e-mail)' || true
  done
fi
if ! email_login_visible; then
  log "FAILURE_SIGNAL=KWAI_EMAIL_LOGIN_NOT_VISIBLE"
  dump_ui && cp /tmp/kwai-ui.xml kwai-login-navigation.xml || true
  exit 35
fi
log "KWAI_EMAIL_LOGIN_FORM_VERIFIED"
if [ -n "${KWAI_LOGIN:-}" ] && [ -n "${KWAI_PASSWORD:-}" ]; then
  log "KWAI_SECRET_CREDENTIALS_PRESENT_AUTOFILL"
  python3 - <<'PY' || true
import os,re,subprocess,xml.etree.ElementTree as ET,time
def call(*args,timeout=8):
 return subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,check=True).stdout
def nodes():
 call('shell','uiautomator','dump','/sdcard/kwai-fill.xml',timeout=15)
 return list(ET.fromstring(call('exec-out','cat','/sdcard/kwai-fill.xml')).iter('node'))
def tap(n):
 m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
 if not m:return False
 a,b,c,d=map(int,m.groups());call('shell','input','tap',str((a+c)//2),str((b+d)//2));return True
def put(value):
 # Do not print secrets. Android input text supports ASCII and encoded spaces.
 if not value or any(ord(ch)<33 or ord(ch)>126 for ch in value):return False
 call('shell','input','text',value.replace('%','%25'))
 return True
try:
 fields=[n for n in nodes() if n.get('class','').endswith('EditText')]
 if not fields:raise RuntimeError('no editable fields')
 for field in fields:
  label=' '.join((field.get('text',''),field.get('content-desc',''),field.get('resource-id',''),field.get('hint',''))).lower()
  if any(x in label for x in ('password','senha')):continue
  if tap(field) and put(os.environ['KWAI_LOGIN']):
   print('KWAI_LOGIN_FIELD_FILLED')
   break
 else:
  if tap(fields[0]) and put(os.environ['KWAI_LOGIN']):print('KWAI_LOGIN_FIELD_FILLED')
 time.sleep(1)
 fields=[n for n in nodes() if n.get('class','').endswith('EditText')]
 pw=[n for n in fields if any(x in ' '.join((n.get('text',''),n.get('content-desc',''),n.get('resource-id',''))).lower() for x in ('password','senha')) or n.get('password')=='true']
 if pw and tap(pw[0]) and put(os.environ['KWAI_PASSWORD']):
  print('KWAI_PASSWORD_FIELD_FILLED')
 else:print('KWAI_PASSWORD_FIELD_NOT_VISIBLE_MANUAL_STEP_REQUIRED')
except Exception as e:
 print('KWAI_AUTOFILL_FAILED',type(e).__name__)
PY
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
