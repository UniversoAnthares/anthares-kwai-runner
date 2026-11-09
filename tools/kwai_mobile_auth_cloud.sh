#!/usr/bin/env bash
set -Eeuo pipefail
: "${KWAI_EXPECTED_ACCOUNT:?expected Kwai identity required}"
: "${KWAI_SESSION_ENCRYPTION_KEY:?encrypted-session key required}"
case "${1:-}" in
  acquire)
    bash kwai_vault_install.sh
    adb shell pm grant com.kwai.video android.permission.POST_NOTIFICATIONS 2>/dev/null || true
    bash kwai_session_state.sh restore || true
    if KWAI_EXPECTED_ACCOUNT="$KWAI_EXPECTED_ACCOUNT" python3 kwai_auth_probe.py >kwai-mobile-auth-proof.txt 2>&1; then
      echo KWAI_MOBILE_RESTORED_AUTH_ALREADY=1 | tee -a kwai-mobile-auth-proof.txt
    else
      python3 tools/kwai_credential_login.py | tee kwai-mobile-login.txt
      sleep 5
      KWAI_EXPECTED_ACCOUNT="$KWAI_EXPECTED_ACCOUNT" python3 kwai_auth_probe.py | tee kwai-mobile-auth-proof.txt
    fi
    grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' kwai-mobile-auth-proof.txt
    grep -qx 'KWAI_IDENTITY_PROFILE_MATCH=1' kwai-mobile-auth-proof.txt
    bash kwai_session_state.sh save | tee kwai-mobile-session-save.txt
    test -s kwai-session.enc
    echo ANTHARES_MOBILE_ACQUIRE=PASS
    ;;
  restore)
    bash kwai_vault_install.sh
    bash kwai_session_state.sh restore | tee kwai-mobile-restore.txt
    adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
    sleep 6
    KWAI_EXPECTED_ACCOUNT="$KWAI_EXPECTED_ACCOUNT" python3 kwai_auth_probe.py | tee kwai-mobile-restore-proof.txt
    grep -qx 'KWAI_AUTH_STATE=AUTHENTICATED_UI' kwai-mobile-restore-proof.txt
    grep -qx 'KWAI_IDENTITY_PROFILE_MATCH=1' kwai-mobile-restore-proof.txt
    echo ANTHARES_MOBILE_CROSS_RUN_RESTORE=PASS
    ;;
  *)
    echo 'KWAI_AUTH_MODE_INVALID' >&2
    exit 2
    ;;
esac
