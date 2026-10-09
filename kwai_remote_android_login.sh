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
  # Use UI text when available; on video overlays UIAutomator may omit text.
  # The onboarding occupies 12 slides, always select RIGHT heart, never left.
  local i dims w h
  dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  w="${dims%x*}"; h="${dims#*x}"
  [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 0
  for i in $(seq 1 15); do
    dump_ui || true
    if grep -Eqi 'Profile|Perfil|Discover|Descobrir|Inbox|Caixa de entrada' /tmp/kwai-ui.xml 2>/dev/null && ! grep -Eqi 'Choose like or dislike|let us know you better' /tmp/kwai-ui.xml 2>/dev/null; then
      log "KWAI_ONBOARDING_MAIN_NAV_VISIBLE"; return 0
    fi
    # Right heart from user screenshot: x≈75%, y≈92.5% of Android viewport.
    adb shell input tap $((w*75/100)) $((h*925/1000)) >/dev/null 2>&1 || true
    log "KWAI_ONBOARDING_RIGHT_HEART_ATTEMPT=$i"
    sleep 2
  done
  log "KWAI_ONBOARDING_RIGHT_HEART_ATTEMPTS_EXHAUSTED"
}

dismiss_onboarding_right_heart(){
  dump_ui || return 0
  if ! grep -Eqi 'Choose like or dislike|let us know you better' /tmp/kwai-ui.xml; then return 0; fi
  local dims w h
  dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  w="${dims%x*}"; h="${dims#*x}"
  [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 0
  # The right-hand heart is centered at ~75% width and 97% height.
  adb shell input tap $((w*75/100)) $((h*94/100)) >/dev/null 2>&1 || true
  log "KWAI_ONBOARDING_RIGHT_HEART_TAPPED"
  sleep 1
}
dismiss_swipe_tutorial(){
  dump_ui || return 0
  if ! grep -Eqi 'Swipe up to watch more|Deslize para cima' /tmp/kwai-ui.xml; then return 0; fi
  local dims w h
  dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
  w="${dims%x*}"; h="${dims#*x}"
  [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]] || return 0
  adb shell input swipe $((w*50/100)) $((h*75/100)) $((w*50/100)) $((h*30/100)) 450 >/dev/null 2>&1 || true
  log "KWAI_SWIPE_TUTORIAL_DISMISSED"
  sleep 2
}
dismiss_resource_overlay(){
  # Kwai's 5% modal is often rendered without accessible UIAutomator labels.
  # First use the accessible Hide button, then device-relative fallback.
  local xy dims w h
  dump_ui || true
  xy="$(python3 - <<'PY'
import re,xml.etree.ElementTree as ET
try:
 root=ET.parse('/tmp/kwai-ui.xml').getroot()
 for n in root.iter('node'):
  label=((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().lower()
  if label == 'hide' or label.startswith('hide '):
   m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
   if m:
    a,b,c,d=map(int,m.groups());print((a+c)//2,(b+d)//2);break
except Exception:pass
PY
)"
  if [ -n "$xy" ]; then
    adb shell input tap $xy >/dev/null 2>&1 || true
    log "KWAI_RESOURCE_HIDE_TAPPED_UI"
  else
    dims="$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)"
    w="${dims%x*}"; h="${dims#*x}"
    if [[ "$w" =~ ^[0-9]+$ && "$h" =~ ^[0-9]+$ ]]; then
      # Screenshot: Hide is centered at x=50%, y≈61% of the Android viewport.
      adb shell input tap $((w*50/100)) $((h*61/100)) >/dev/null 2>&1 || true
      log "KWAI_RESOURCE_HIDE_TAPPED_FALLBACK"
    fi
  fi
  sleep 1
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
  if kwai_foreground && ! google_sso_foreground; then dismiss_notification_permission; complete_kwai_interest_onboarding; dismiss_resource_overlay; dismiss_swipe_tutorial; fi
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
import re,xml.etree.ElementTree as ET
try: root=ET.parse('/tmp/kwai-ui.xml').getroot()
except Exception: raise SystemExit(1)
nodes=list(root.iter('node'))
s=' '.join(' '.join((n.get('text',''),n.get('content-desc',''),n.get('resource-id',''))) for n in nodes).lower()
fields=sum(n.get('class','').endswith('EditText') for n in nodes)
auth=re.search(r'log.?in|sign.?in|entrar|password|senha|phone number|e-?mail|verification code|código de verificação|send code|continuar com',s)
focus=__import__('subprocess').run(['adb','shell','dumpsys','window'],capture_output=True,text=True).stdout.lower()
google='com.google.android.gms' in focus
raise SystemExit(0 if (not google and (auth or (fields and re.search(r'continue|continuar|next|próximo',s)))) else 1)
PY
}
login_lock(){
  log "LOGIN_SURFACE_DETECTED"
  log "LOCKED_ON_LOGIN"
  adb exec-out screencap -p > kwai-login-detected.png 2>/dev/null || true
  dump_ui && cp /tmp/kwai-ui.xml kwai-login-detected.xml || true
  adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' > kwai-login-focus.txt || true
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
# Retry Google entry across delayed screens and transient UIAutomator failures.
# Never infer success from a tap alone: require Google SSO foreground.
for welcome_attempt in $(seq 1 24); do
  if google_sso_foreground; then
    log "KWAI_GOOGLE_SSO_REACHED_AFTER_WELCOME_CLICK"
    break
  fi
  dump_ui || true
  if grep -Eqi 'Continue with Google|Continuar com Google|Google' /tmp/kwai-ui.xml 2>/dev/null; then
    log "KWAI_GOOGLE_ENTRY_DETECTED_ATTEMPT_$welcome_attempt"
    if tap_label '(Continue with Google|Continuar com Google)' || tap_label 'Google'; then
      log "KWAI_GOOGLE_ENTRY_TAP_SENT_ATTEMPT_$welcome_attempt"
    else
      log "KWAI_GOOGLE_ENTRY_LABEL_TAP_FAILED_$welcome_attempt"
    fi
  else
    log "KWAI_GOOGLE_ENTRY_NOT_VISIBLE_ATTEMPT_$welcome_attempt"
  fi
  sleep 3
done
if google_sso_foreground; then
  log "KWAI_GOOGLE_ENTRY_VERIFIED"
else
  log "KWAI_GOOGLE_ENTRY_UNVERIFIED_MANUAL_HANDOFF"
fi
if ! email_login_visible; then
  complete_kwai_interest_onboarding || true
  dismiss_swipe_tutorial || true
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
  # UIAutomator sometimes omits the bottom Profile label on Kwai's video feed.
  # Tap the known rightmost bottom navigation item using screen-relative bounds.
  if ! email_login_visible; then
    log "KWAI_PROFILE_BOTTOM_RIGHT_FALLBACK"
    adb shell input tap $((width*94/100)) $((height*95/100)) >/dev/null 2>&1 || true
    sleep 3
  fi
  for _ in $(seq 1 5); do
    complete_kwai_interest_onboarding || true
    dismiss_resource_overlay || true
    dismiss_swipe_tutorial || true
    email_login_visible && break
    if google_sso_foreground; then log "GOOGLE_SSO_ACTIVE_DO_NOT_INTERRUPT"; break; fi
    tap_label '(log[ -]?in|sign[ -]?in|entrar|fazer login|cadastre-se|sign up|register)' || true
    email_login_visible && break
    tap_label '(other methods|other ways|more options|outras opções|outras formas|use another method)' || true
    email_login_visible && break
    tap_label '(e-?mail|email address|endereço de e-mail|continuar com e-mail)' || true
  done
fi
if ! email_login_visible && ! google_sso_foreground; then
  log "FAILURE_SIGNAL=KWAI_EMAIL_LOGIN_NOT_VISIBLE"
  dump_ui && { cp /tmp/kwai-ui.xml kwai-login-navigation.xml; grep -Eo 'text="[^"]*"|content-desc="[^"]*"' /tmp/kwai-ui.xml | tail -65 >> "$REPORT" || true; } || true
  log "LOGIN_DISCOVERY_MANUAL_HANDOFF_45_MINUTES"
  # Do not abort: the owner may still navigate manually to email/password on a slow remote screen.
fi
if email_login_visible; then login_lock; log "KWAI_EMAIL_LOGIN_FORM_VERIFIED"; else log "GOOGLE_SSO_HANDOFF_WAITING"; fi
if [ "${KWAI_AUTOFILL_ENABLED:-0}" = "1" ] && [ -n "${KWAI_LOGIN:-}" ] && [ -n "${KWAI_PASSWORD:-}" ]; then
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
LOGIN_DEADLINE=$((SECONDS+2700))
SSO_WAS_ACTIVE=0
SSO_STARTED_AT=0
OVERLAY_LAST_CHECK=0
# Google account setup may show a separate consent page after credentials.
# Automatically accept only the explicit Google welcome agreement screen.
GOOGLE_AGREEMENT_LAST_CHECK=0
while [ "$SECONDS" -lt "$LOGIN_DEADLINE" ]; do
  if google_sso_foreground; then
    if [ $((SECONDS-GOOGLE_AGREEMENT_LAST_CHECK)) -ge 5 ]; then
      GOOGLE_AGREEMENT_LAST_CHECK=$SECONDS
      dump_ui || true
      if grep -Eqi 'I agree|Concordo' /tmp/kwai-ui.xml 2>/dev/null && grep -Eqi 'Google Terms of Service|Google Play Terms of Service|Google Privacy Policy|Termos de Serviço do Google' /tmp/kwai-ui.xml 2>/dev/null; then
        if tap_label '^(I agree|Concordo)
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
      # Login is locked: no automatic overlay or onboarding taps.
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
log "FAIL: login-window-expired-2700s"; exit 28
; then
          log "GOOGLE_WELCOME_AGREEMENT_BUTTON_TAPPED"
        else
          log "GOOGLE_WELCOME_AGREEMENT_BUTTON_NOT_CLICKED"
        fi
      fi
    fi
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
      # Login is locked: no automatic overlay or onboarding taps.
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
log "FAIL: login-window-expired-2700s"; exit 28
