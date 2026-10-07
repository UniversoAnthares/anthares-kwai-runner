#!/usr/bin/env bash
set -Eeuo pipefail

if ! bash kwai_headless_login.sh; then
  echo "KWAI_SESSION_NOT_READY=1"
  cat kwai-headless-status.txt 2>/dev/null || true
  exit 64
fi

AUTH_OUT="$(python3 kwai_auth_probe.py 2>&1)" || {
  echo "$AUTH_OUT"
  exit 65
}
echo "$AUTH_OUT"
echo "$AUTH_OUT" | grep -q 'KWAI_AUTH_STATE=AUTHENTICATED_UI' || exit 65

NOW="$(date +%s)"
export KWAI_AUTH_READY_PROOF="{\"state\":\"READY\",\"account\":\"${KWAI_EXPECTED_ACCOUNT}\",\"observed_at\":${NOW},\"proof_id\":\"run-${GITHUB_RUN_ID}\"}"

if bash kwai_run_next_job.sh >kwai-publication.log 2>&1; then
  rc=0
else
  rc=$?
fi

cat kwai-publication.log

if grep -q 'KWAI_QUEUE_EMPTY' kwai-publication.log; then
  echo "KWAI_QUEUE_EMPTY_OK=1"
  exit 0
fi

exit "$rc"
