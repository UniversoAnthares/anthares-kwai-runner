#!/usr/bin/env bash
set -Eeuo pipefail
STATE_FILE="${KWAI_SESSION_FILE:-kwai-session.enc}"

echo "KWAI_SESSION_RESTORE_GATE_BEGIN"
adb wait-for-device
if ! adb shell pm path com.kwai.video 2>/dev/null | grep -q 'package:'; then
  [ -s kwai-vault/MANIFEST.tsv ] || { echo "FAILURE_SIGNAL=VALIDATED_VAULT_MISSING_BEFORE_RESTORE"; exit 29; }
  bash kwai_vault_install.sh
  echo "KWAI_INSTALLED_FOR_SESSION_RESTORE"
fi

if [ -s "$STATE_FILE" ]; then
  echo "KWAI_SESSION_RESTORE_ATTEMPTED"
  if bash kwai_session_state.sh restore; then
    adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
    sleep 7
    if python3 kwai_auth_probe.py >/tmp/kwai-restored-auth-probe.log 2>&1 && grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' /tmp/kwai-restored-auth-probe.log; then
      echo "KWAI_SESSION_RESTORE_CONFIRMED"
      adb exec-out screencap -p > kwai-remote-ready.png 2>/dev/null || true
      exit 0
    fi
    echo "KWAI_SESSION_RESTORE_NOT_AUTHENTICATED"
    grep -E '^KWAI_AUTH_STATE=' /tmp/kwai-restored-auth-probe.log 2>/dev/null || true
  else
    echo "KWAI_SESSION_RESTORE_APPLY_FAILED"
  fi
else
  echo "KWAI_SESSION_CACHE_MISS_BEFORE_LOGIN"
fi

echo "KWAI_SESSION_RESTORE_GATE_FALLBACK_INTERACTIVE"
rm -f /tmp/kwai-auth-network-error-detected /tmp/anthares-android-done /tmp/kwai-autofill-watcher.log

python3 - <<'PATCHPY'
from pathlib import Path
src=Path('kwai_remote_android_login.sh').read_text()

old="""    if kwai_foreground && [ $((SECONDS-OVERLAY_LAST_CHECK)) -ge 3 ]; then
      OVERLAY_LAST_CHECK=$SECONDS
      dismiss_notification_permission
      # Login is locked: no automatic overlay or onboarding taps.
    fi"""
new="""    # Stable owner-login phase: notification permission was pre-granted.
    # Do not start another UIAutomator client here."""
if old in src:
    src=src.replace(old,new,1)
    print('KWAI_RUNTIME_UIAUTOMATOR_COLLISION_PATCHED')
else:
    print('KWAI_RUNTIME_UIAUTOMATOR_PATCH_PATTERN_NOT_FOUND')

old2="""    dump_ui || true
    if grep -Eqi 'Profile|Perfil|Discover|Descobrir|Inbox|Caixa de entrada' /tmp/kwai-ui.xml 2>/dev/null && ! grep -Eqi 'Choose like or dislike|let us know you better' /tmp/kwai-ui.xml 2>/dev/null; then
      log \"KWAI_ONBOARDING_MAIN_NAV_VISIBLE\"; return 0
    fi"""
new2="""    dump_ui || true
    if grep -Eqi 'Select your interests|bt_interest_skip_top_right|selected and continue' /tmp/kwai-ui.xml 2>/dev/null; then
      adb shell input tap $((w*90/100)) $((h*9/100)) >/dev/null 2>&1 || true
      log \"KWAI_INTEREST_SELECTION_SKIPPED\"
      sleep 3
      continue
    fi
    if grep -Eqi 'Profile|Perfil|Discover|Descobrir|Inbox|Caixa de entrada' /tmp/kwai-ui.xml 2>/dev/null && ! grep -Eqi 'Choose like or dislike|let us know you better|Select your interests|selected and continue' /tmp/kwai-ui.xml 2>/dev/null; then
      log \"KWAI_ONBOARDING_MAIN_NAV_VISIBLE\"; return 0
    fi"""
if old2 in src:
    src=src.replace(old2,new2,1)
    print('KWAI_RUNTIME_INTEREST_SKIP_PATCHED')
else:
    print('KWAI_RUNTIME_INTEREST_SKIP_PATTERN_NOT_FOUND')

start=src.find('email_login_visible(){')
end=src.find('\nlogin_lock(){', start)
if start >= 0 and end > start:
    strict="""email_login_visible(){
  dump_ui || return 1
  python3 - <<'PY'
import xml.etree.ElementTree as ET
try: root=ET.parse('/tmp/kwai-ui.xml').getroot()
except Exception: raise SystemExit(1)
nodes=list(root.iter('node'))
fields=[n for n in nodes if n.get('class','').endswith('EditText')]
focus=__import__('subprocess').run(['adb','shell','dumpsys','window'],capture_output=True,text=True).stdout.lower()
google='com.google.android.gms' in focus
raise SystemExit(0 if (not google and len(fields)>0) else 1)
PY
}"""
    src=src[:start]+strict+src[end:]
    print('KWAI_RUNTIME_STRICT_LOGIN_FORM_PATCHED')
else:
    print('KWAI_RUNTIME_STRICT_LOGIN_FORM_PATTERN_NOT_FOUND')

src=src.replace("1) tap_label '^(Profile|Perfil|Eu|Me)$' || true ;;", "1) tap_label '^(Log In|Sign In|Entrar|Login)$' || tap_label '^(Profile|Perfil|Eu|Me)$' || true ;;", 1)
print('KWAI_RUNTIME_FEED_LOGIN_TAB_FIRST')

Path('/tmp/kwai_remote_android_login.runtime.sh').write_text(src)
PATCHPY

python3 kwai_login_autofill_watcher.py >/tmp/kwai-autofill-watcher.log 2>&1 &
WATCHER_PID=$!
bash /tmp/kwai_remote_android_login.runtime.sh &
LOGIN_PID=$!

while kill -0 "$LOGIN_PID" 2>/dev/null; do
  if [ -f /tmp/kwai-auth-network-error-detected ]; then
    echo "FAILURE_SIGNAL=KWAI_POST_PASSWORD_NETWORK_ERROR"
    sleep 5
    kill "$LOGIN_PID" 2>/dev/null || true
    set +e; wait "$LOGIN_PID"; set -e
    kill "$WATCHER_PID" 2>/dev/null || true
    cat /tmp/kwai-autofill-watcher.log 2>/dev/null || true
    exit 41
  fi
  if ! kill -0 "$WATCHER_PID" 2>/dev/null; then
    set +e
    wait "$WATCHER_PID"
    WATCHER_RC=$?
    set -e
    cat /tmp/kwai-autofill-watcher.log 2>/dev/null || true
    if [ "$WATCHER_RC" -eq 0 ] && [ -f /tmp/anthares-android-done ]; then
      echo "KWAI_AUTOFILL_WATCHER_AUTH_SIGNAL_WAITING_FOR_MAIN"
    else
      echo "FAILURE_SIGNAL=KWAI_AUTOFILL_WATCHER_EXIT_${WATCHER_RC}"
      kill "$LOGIN_PID" 2>/dev/null || true
      set +e; wait "$LOGIN_PID"; set -e
      exit "$WATCHER_RC"
    fi
  fi
  sleep 1
done

set +e
wait "$LOGIN_PID"
RC=$?
set -e
kill "$WATCHER_PID" 2>/dev/null || true
wait "$WATCHER_PID" 2>/dev/null || true
cat /tmp/kwai-autofill-watcher.log 2>/dev/null || true
exit "$RC"
