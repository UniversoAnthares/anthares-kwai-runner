#!/usr/bin/env bash
set -Eeuo pipefail
# Canonical single-job executor. It is safe to call only on a cloud executor with the authenticated Android session.
CLAIM_ENV="$(mktemp)"
trap 'rm -f "$CLAIM_ENV"' EXIT
GITHUB_ENV="$CLAIM_ENV" bash kwai_claim_job.sh
set -a
# shellcheck disable=SC1090
source "$CLAIM_ENV"
set +a
python3 kwai_real_publish_promotion_gate.py
: "${KWAI_VIDEO_URL:?leased job lacks video_url}"
: "${KWAI_VIDEO_TITLE:?leased job lacks video_title}"
: "${KWAI_EXPECTED_ACCOUNT:?leased job lacks expected_account}"
set +e
bash kwai_publish.sh
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  grep -q '^STATE=CONFIRMED$' kwai-publish-status.txt
  echo "KWAI_JOB_TERMINAL_CONFIRMED"
  exit 0
fi
if [ "$rc" -ne 90 ]; then
  echo "KWAI_JOB_FAILED_SAFE RC=$rc"
  exit "$rc"
fi
# Only UNCERTAIN crosses into reconciliation. Never call the publisher again.
sha="$(sed -n 's/^MEDIA_SHA256=//p' kwai-publish-status.txt | tail -1)"
test -n "$sha" || { echo "KWAI_RECONCILE_BLOCKED_NO_MEDIA_IDENTITY"; exit 90; }
export KWAI_MEDIA_SHA256="$sha"
set +e
bash kwai_reconcile_uncertain.sh
rrc=$?
set -e
if [ "$rrc" -eq 0 ]; then
  grep -q '^STATE=CONFIRMED SOURCE=RECONCILIATION$' kwai-reconcile-status.txt
  echo "KWAI_JOB_TERMINAL_RECONCILED"
  exit 0
fi
echo "KWAI_JOB_REMAINS_UNCERTAIN"
exit 90
