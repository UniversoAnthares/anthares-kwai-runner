#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/kwai_reconcile_uncertain.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

run_case(){
  local name="$1" verifier_rc="$2" verifier_body="$3" queue_rc="$4" expected_rc="$5" expected_state="$6" expected_calls="$7"
  local d="$tmp/$name"; mkdir -p "$d"
  cp "$SCRIPT" "$d/kwai_reconcile_uncertain.sh"
  cat >"$d/kwai_verify_publication.py" <<PY
import sys
print("")
PY
  # Write exact fixture output without shell interpolation surprises.
  printf '%s\n' "$verifier_body" >"$d/verifier.out"
  cat >"$d/kwai_verify_publication.py" <<'PY'
from pathlib import Path
import os,sys
print(Path("verifier.out").read_text(), end="")
sys.exit(int(os.environ["FIXTURE_VERIFY_RC"]))
PY
  cat >"$d/kwai_queue_state.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s|%s\n' "$1" "${2:-}" >> queue.calls
exit "${FIXTURE_QUEUE_RC}"
SH
  chmod +x "$d/kwai_queue_state.sh"
  set +e
  (cd "$d" && env KWAI_QUEUE_JOB_ID=job-1 KWAI_VIDEO_TITLE='Canary title' KWAI_EXPECTED_ACCOUNT='expected-account' KWAI_MEDIA_SHA256='0123456789abcdef' FIXTURE_VERIFY_RC="$verifier_rc" FIXTURE_QUEUE_RC="$queue_rc" bash ./kwai_reconcile_uncertain.sh >case.out 2>&1)
  rc=$?
  set -e
  test "$rc" = "$expected_rc" || { echo "$name: rc=$rc expected=$expected_rc"; cat "$d/case.out"; exit 1; }
  grep -q "$expected_state" "$d/case.out" || { echo "$name: missing state $expected_state"; cat "$d/case.out"; exit 1; }
  calls=0; test ! -f "$d/queue.calls" || calls="$(wc -l <"$d/queue.calls" | tr -d ' ')"
  test "$calls" = "$expected_calls" || { echo "$name: queue calls=$calls expected=$expected_calls"; exit 1; }
  if [ "$calls" = "1" ]; then grep -q '^reconcile|' "$d/queue.calls"; fi
}

run_case confirmed 0 $'KWAI_CONFIRMATION_EVIDENCE=eyJqb2JfaWQiOiJqb2ItMSIsIm1lZGlhX3NoYTI1NiI6IjAxMjM0NTY3ODlhYmNkZWYiLCJleHBlY3RlZF9hY2NvdW50IjoiZXhwZWN0ZWQtYWNjb3VudCIsIm9ic2VydmVkX2FjY291bnRfbWF0Y2giOnRydWUsImV4cGVjdGVkX3RpdGxlIjoiQ2FuYXJ5IHRpdGxlIiwib2JzZXJ2ZWRfdGl0bGVfbWF0Y2giOnRydWUsInByb2ZpbGVfc3RhdGUiOiJyZWFkeSJ9\nKWAI_PUBLICATION_SPECIFICALLY_VERIFIED' 0 0 'STATE=CONFIRMED SOURCE=RECONCILIATION' 1
run_case verifier_negative 7 'PROFILE_LOADING' 0 90 'STATE=UNCERTAIN REASON=reconcile-not-positively-verified' 0
run_case evidence_missing 0 'KWAI_PUBLICATION_SPECIFICALLY_VERIFIED' 0 90 'STATE=UNCERTAIN REASON=reconcile-evidence-missing' 0
run_case specific_missing 0 'KWAI_CONFIRMATION_EVIDENCE=weak-proof' 0 90 'STATE=UNCERTAIN REASON=reconcile-specific-proof-missing' 0
run_case central_reject 0 $'KWAI_CONFIRMATION_EVIDENCE=eyJqb2JfaWQiOiJqb2ItMSIsIm1lZGlhX3NoYTI1NiI6IjAxMjM0NTY3ODlhYmNkZWYiLCJleHBlY3RlZF9hY2NvdW50IjoiZXhwZWN0ZWQtYWNjb3VudCIsIm9ic2VydmVkX2FjY291bnRfbWF0Y2giOnRydWUsImV4cGVjdGVkX3RpdGxlIjoiQ2FuYXJ5IHRpdGxlIiwib2JzZXJ2ZWRfdGl0bGVfbWF0Y2giOnRydWUsInByb2ZpbGVfc3RhdGUiOiJyZWFkeSJ9\nKWAI_PUBLICATION_SPECIFICALLY_VERIFIED' 9 90 'STATE=UNCERTAIN REASON=central-reconcile-not-acknowledged' 1

! grep -Eq 'kwai_publish_video|[[:space:]]commit([[:space:]]|$)|input tap.*Publish|text=Publish' "$SCRIPT"
echo KWAI_UNCERTAIN_RECONCILE_EXECUTABLE_OK
