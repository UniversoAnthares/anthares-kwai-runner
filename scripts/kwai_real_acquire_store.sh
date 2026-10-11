#!/usr/bin/env bash
# Real Kwai credential login recovery. This file is invoked with bash explicitly,
# avoiding the Android emulator action's POSIX /usr/bin/sh wrapper.
set -eu
: "${KWAI_LOGIN:?KWAI_LOGIN secret is required}"
: "${KWAI_PASSWORD:?KWAI_PASSWORD secret is required}"
: > kwai-mobile-login.txt
login_ok=0
attempt=1
while [ "$attempt" -le 3 ]; do
  echo "KWAI_REAL_LOGIN_ATTEMPT=$attempt"
  if python3 tools/kwai_credential_login.py 2>&1 | tee -a kwai-mobile-login.txt; then
    login_ok=1
    break
  fi
  adb shell am force-stop com.kwai.video >/dev/null 2>&1 || true
  adb shell svc wifi enable >/dev/null 2>&1 || true
  adb shell svc data enable >/dev/null 2>&1 || true
  sleep 4
  adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
  sleep 10
  python3 tools/kwai_login_surface_recovery.py || true
  attempt=$((attempt + 1))
done
if [ "$login_ok" -ne 1 ]; then
  echo "KWAI_REAL_LOGIN_RETRIES_EXHAUSTED"
  exit 1
fi
sleep 5
KWAI_EXPECTED_ACCOUNT="${KWAI_EXPECTED_ACCOUNT:?expected account required}" python3 kwai_auth_probe.py | tee kwai-mobile-auth-proof.txt
grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' kwai-mobile-auth-proof.txt
grep -qx 'KWAI_IDENTITY_PROFILE_MATCH=1' kwai-mobile-auth-proof.txt
bash kwai_session_state.sh save | tee kwai-mobile-session-save.txt
test -s kwai-session.enc
echo ANTHARES_MOBILE_ACQUIRE=PASS
