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
    cat /tmp/kwai-restored-auth-probe.log 2>/dev/null | grep -E '^KWAI_AUTH_STATE=' || true
  else
    echo "KWAI_SESSION_RESTORE_APPLY_FAILED"
  fi
else
  echo "KWAI_SESSION_CACHE_MISS_BEFORE_LOGIN"
fi

echo "KWAI_SESSION_RESTORE_GATE_FALLBACK_INTERACTIVE"
exec bash kwai_remote_android_login.sh
