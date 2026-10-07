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
curl -fL --retry 3 --connect-timeout 15 --max-time 300 -o /tmp/anthares-upload.mp4 "$KWAI_VIDEO_URL"
test -s /tmp/anthares-upload.mp4 || { log "STATE=FAILED_SAFE REASON=empty-video"; exit 80; }
head -c 64 /tmp/anthares-upload.mp4 | grep -a -q 'ftyp' || { log "STATE=FAILED_SAFE REASON=invalid-mp4"; exit 81; }
KWAI_MEDIA_SHA256="$(sha256sum /tmp/anthares-upload.mp4 | awk '{print $1}')"
KWAI_MEDIA_SIZE="$(stat -c %s /tmp/anthares-upload.mp4)"
KWAI_MEDIA_NAME="anthares-${JOB_SAFE//[^A-Za-z0-9._-]/_}-${KWAI_MEDIA_SHA256:0:12}.mp4"
KWAI_ANDROID_VIDEO="/sdcard/Movies/AntharesPublish/$KWAI_MEDIA_NAME"
export KWAI_MEDIA_SHA256 KWAI_MEDIA_SIZE KWAI_MEDIA_NAME KWAI_ANDROID_VIDEO
log "MEDIA_SHA256=$KWAI_MEDIA_SHA256"
log "MEDIA_SIZE=$KWAI_MEDIA_SIZE"
log "MEDIA_NAME=$KWAI_MEDIA_NAME"

adb shell mkdir -p /sdcard/Movies/AntharesPublish
# This directory is owned by this publication harness; never clear general user media.
adb shell 'rm -f /sdcard/Movies/AntharesPublish/* 2>/dev/null || true'
adb push /tmp/anthares-upload.mp4 "$KWAI_ANDROID_VIDEO" >/dev/null
adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://$KWAI_ANDROID_VIDEO" >/dev/null
sleep 2
REMOTE_SIZE="$(adb shell stat -c %s "$KWAI_ANDROID_VIDEO" | tr -d '\r')"
test "$REMOTE_SIZE" = "$KWAI_MEDIA_SIZE" || { log "STATE=FAILED_SAFE REASON=android-size-mismatch"; exit 84; }
COUNT="$(adb shell content query --uri content://media/external/video/media --projection _id:_display_name:_size 2>/dev/null | tr -d '\r' | grep -F "_display_name=$KWAI_MEDIA_NAME" | grep -F "_size=$KWAI_MEDIA_SIZE" | wc -l | tr -d ' ')"
test "$COUNT" = "1" || { log "STATE=FAILED_SAFE REASON=mediastore-identity-count-$COUNT"; exit 85; }
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
  log "STATE=UNCERTAIN REASON=central-complete-not-acknowledged"
  exit 90
fi
log "STATE=CONFIRMED"
