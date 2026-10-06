#!/usr/bin/env bash
set -Eeuo pipefail

: "${KWAI_QUEUE_JOB_ID:?KWAI_QUEUE_JOB_ID is required}"
: "${KWAI_VIDEO_TITLE:?KWAI_VIDEO_TITLE is required}"
: "${KWAI_EXPECTED_ACCOUNT:?KWAI_EXPECTED_ACCOUNT is required}"
: "${KWAI_MEDIA_SHA256:?KWAI_MEDIA_SHA256 is required}"

REPORT="${KWAI_RECONCILE_REPORT:-kwai-reconcile-status.txt}"
: >"$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }

# Reconciliation is deliberately observation-only. It never imports media,
# prepares a composer, invokes commit, or touches the Publish control.
log "STATE=RECONCILING JOB_ID=$KWAI_QUEUE_JOB_ID"

set +e
VERIFY_OUT="$(python3 kwai_verify_publication.py 2>&1)"
VRC=$?
set -e
printf '%s\n' "$VERIFY_OUT" | tee -a "$REPORT"

if [ "$VRC" -ne 0 ]; then
  log "STATE=UNCERTAIN REASON=reconcile-not-positively-verified VERIFY_RC=$VRC"
  exit 90
fi

EVIDENCE="$(printf '%s\n' "$VERIFY_OUT" | sed -n 's/^KWAI_CONFIRMATION_EVIDENCE=//p' | tail -1)"
test -n "$EVIDENCE" || {
  log "STATE=UNCERTAIN REASON=reconcile-evidence-missing"
  exit 90
}
printf '%s\n' "$VERIFY_OUT" | grep -q '^KWAI_PUBLICATION_SPECIFICALLY_VERIFIED
if ! bash kwai_queue_state.sh reconcile "$EVIDENCE" >>"$REPORT" 2>&1; then
  log "STATE=UNCERTAIN REASON=central-reconcile-not-acknowledged"
  exit 90
fi

log "STATE=CONFIRMED SOURCE=RECONCILIATION"
 || {
  log "STATE=UNCERTAIN REASON=reconcile-specific-proof-missing"
  exit 90
}

# Bind verifier evidence to this exact queued job/media/account/title before
# allowing central reconciliation. A stale or forged verifier token must never
# confirm a different UNCERTAIN job.
if ! python3 - "$EVIDENCE" "$KWAI_QUEUE_JOB_ID" "$KWAI_MEDIA_SHA256" "$KWAI_EXPECTED_ACCOUNT" "$KWAI_VIDEO_TITLE" <<'PY'
import base64,json,sys
token,job,sha,account,title=sys.argv[1:]
try:
    raw=base64.urlsafe_b64decode(token + "="*((4-len(token)%4)%4))
    d=json.loads(raw.decode("utf-8"))
except Exception:
    raise SystemExit(1)
required={
    "job_id":job,
    "media_sha256":sha,
    "expected_account":account,
    "expected_title":title,
    "observed_account_match":True,
    "observed_title_match":True,
    "profile_state":"ready",
}
if any(d.get(k)!=v for k,v in required.items()):
    raise SystemExit(1)
PY
then
  log "STATE=UNCERTAIN REASON=reconcile-evidence-identity-mismatch"
  exit 90
fi

export KWAI_CONFIRMATION_EVIDENCE="$EVIDENCE"
if ! bash kwai_queue_state.sh reconcile "$EVIDENCE" >>"$REPORT" 2>&1; then
  log "STATE=UNCERTAIN REASON=central-reconcile-not-acknowledged"
  exit 90
fi

log "STATE=CONFIRMED SOURCE=RECONCILIATION"
