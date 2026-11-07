#!/usr/bin/env bash
set -Eeuo pipefail

: "${KWAI_LEASE_GENERATION:?KWAI_LEASE_GENERATION is required for fenced publication}"
if [ "${KWAI_HEARTBEAT_ACTIVE:-0}" != "1" ]; then
  export KWAI_HEARTBEAT_ACTIVE=1
  exec bash kwai_queue_heartbeat.sh bash "$0" "$@"
fi
REPORT="kwai-publish-status.txt"
: >"$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }

: "${KWAI_VIDEO_URL:?KWAI_VIDEO_URL is required}"
: "${KWAI_VIDEO_TITLE:?KWAI_VIDEO_TITLE is required}"
: "${KWAI_QUEUE_JOB_ID:?KWAI_QUEUE_JOB_ID is required for safe publication}"
: "${KWAI_EXPECTED_ACCOUNT:?KWAI_EXPECTED_ACCOUNT is required for positive verification}"
JOB_SAFE="$KWAI_QUEUE_JOB_ID"
STARTED_ACK=0

mark_uncertain(){
  local reason="${1:-unknown}"
  if [ "$STARTED_ACK" = "1" ]; then
    set +e
    bash kwai_queue_state.sh fail "$reason" >>"$REPORT" 2>&1
    set -e
  fi
}

log "STATE=MEDIA_PREPARING"
# The queue's job_id + content digest bind the transfer to exactly one cut.
# Staging is performed in the cloud runner; no Windows/PC path is used.
if ! python3 tools/kwai_media_stage.py > /tmp/kwai-media-stage.out 2>&1; then
  cat /tmp/kwai-media-stage.out | tee -a "$REPORT"
  log "STATE=FAILED_SAFE REASON=remote-media-stage-failed"
  exit 84
fi
grep -qx 'KWAI_MEDIA_STAGE=READY' /tmp/kwai-media-stage.out || {
  log "STATE=FAILED_SAFE REASON=remote-media-ready-missing"; exit 85;
}
mapfile -t VERIFIED_MEDIA < <(python3 - <<'PY'
import json
p=json.load(open("kwai-media-ready.json",encoding="utf-8"))
assert p["schema"]=="anthares.kwai.media-ready.v1"
for key in ("sha256","size","name","remote_path","media_uri"):
 print(p[key])
PY
)
[ "${#VERIFIED_MEDIA[@]}" -eq 5 ] || { log "STATE=FAILED_SAFE REASON=remote-media-proof-invalid"; exit 85; }
KWAI_MEDIA_SHA256="${VERIFIED_MEDIA[0]}"
KWAI_MEDIA_SIZE="${VERIFIED_MEDIA[1]}"
KWAI_MEDIA_NAME="${VERIFIED_MEDIA[2]}"
KWAI_ANDROID_VIDEO="${VERIFIED_MEDIA[3]}"
KWAI_ANDROID_MEDIA_URI="${VERIFIED_MEDIA[4]}"
export KWAI_MEDIA_SHA256 KWAI_MEDIA_SIZE KWAI_MEDIA_NAME KWAI_ANDROID_VIDEO KWAI_ANDROID_MEDIA_URI
log "MEDIA_SHA256=$KWAI_MEDIA_SHA256"
log "MEDIA_SIZE=$KWAI_MEDIA_SIZE"
log "MEDIA_NAME=$KWAI_MEDIA_NAME"
log "STATE=MEDIA_IMPORTED MEDIASTORE_MATCHES=1"

# Transitional gate: real workflow remains quarantined until kwai-login supplies READY.
python3 kwai_auth_probe.py >>"$REPORT" 2>&1 || { log "STATE=SESSION_EXPIRED"; exit 82; }

# PREPARE must end before the irreversible publish boundary.
set +e
python3 kwai_publish_video.py prepare >>"$REPORT" 2>&1
prc=$?
set -e
if [ "$prc" -ne 0 ]; then log "STATE=FAILED_SAFE PREPARE_RC=$prc"; exit "$prc"; fi
grep -q '^STATE=READY_TO_PUBLISH$' "$REPORT" || { log "STATE=FAILED_SAFE REASON=ready-to-publish-proof-missing"; exit 87; }

# Central started acknowledgement is mandatory before commit. This call also rejects stale Worker versions.
bash kwai_queue_state.sh started >>"$REPORT" 2>&1 || { log "STATE=FAILED_SAFE REASON=central-started-not-acknowledged"; exit 86; }
STARTED_ACK=1

set +e
python3 kwai_publish_video.py commit >>"$REPORT" 2>&1
rc=$?
set -e
if [ "$rc" -ne 0 ]; then
  mark_uncertain "commit-rc-$rc"
  log "STATE=UNCERTAIN PUBLISH_FLOW_RC=$rc"
  exit 90
fi

log "STATE=VERIFYING"
set +e
VERIFY_OUT="$(python3 kwai_verify_publication.py 2>&1)"
vrc=$?
set -e
printf '%s\n' "$VERIFY_OUT" | tee -a "$REPORT"
if [ "$vrc" -ne 0 ]; then
  mark_uncertain "verification-rc-$vrc"
  log "STATE=UNCERTAIN REASON=publication-not-positively-verified"
  exit 90
fi
KWAI_CONFIRMATION_EVIDENCE="$(printf '%s\n' "$VERIFY_OUT" | sed -n 's/^KWAI_CONFIRMATION_EVIDENCE=//p' | tail -1)"
test -n "$KWAI_CONFIRMATION_EVIDENCE" || {
  mark_uncertain "verification-evidence-missing"
  log "STATE=UNCERTAIN REASON=confirmation-evidence-missing"
  exit 90
}
export KWAI_CONFIRMATION_EVIDENCE

# CONFIRMED is emitted only after the controller accepts the specific evidence.
if ! bash kwai_queue_state.sh complete "$KWAI_CONFIRMATION_EVIDENCE" >>"$REPORT" 2>&1; then
  mark_uncertain "central-complete-not-acknowledged"
  log "STATE=UNCERTAIN REASON=central-complete-not-acknowledged"
  exit 90
fi
log "STATE=CONFIRMED"
