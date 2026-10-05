#!/usr/bin/env bash
set -Eeuo pipefail
REPORT="kwai-publish-status.txt"
: >"$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }

: "${KWAI_VIDEO_URL:?KWAI_VIDEO_URL is required}"
: "${KWAI_VIDEO_TITLE:?KWAI_VIDEO_TITLE is required}"
JOB_SAFE="${KWAI_QUEUE_JOB_ID:-manual-${GITHUB_RUN_ID:-local}}"

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
adb shell rm -f '/sdcard/Movies/AntharesPublish/*'
adb push /tmp/anthares-upload.mp4 "$KWAI_ANDROID_VIDEO" >/dev/null
adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://$KWAI_ANDROID_VIDEO" >/dev/null
sleep 2
REMOTE_SIZE="$(adb shell stat -c %s "$KWAI_ANDROID_VIDEO" | tr -d '\r')"
test "$REMOTE_SIZE" = "$KWAI_MEDIA_SIZE" || { log "STATE=FAILED_SAFE REASON=android-size-mismatch"; exit 84; }
COUNT="$(adb shell content query --uri content://media/external/video/media --projection _id:_display_name:_size 2>/dev/null | tr -d '\r' | grep -F "_display_name=$KWAI_MEDIA_NAME" | grep -F "_size=$KWAI_MEDIA_SIZE" | wc -l | tr -d ' ')"
test "$COUNT" = "1" || { log "STATE=FAILED_SAFE REASON=mediastore-identity-count-$COUNT"; exit 85; }
log "STATE=MEDIA_IMPORTED MEDIASTORE_MATCHES=1"

python3 kwai_auth_probe.py >>"$REPORT" 2>&1 || { log "STATE=SESSION_EXPIRED"; exit 82; }
set +e
python3 kwai_publish_video.py >>"$REPORT" 2>&1
rc=$?
set -e
if [ "$rc" -eq 90 ]; then log "STATE=UNCERTAIN"; exit 90; fi
if [ "$rc" -ne 0 ]; then log "STATE=FAILED_SAFE PUBLISH_FLOW_RC=$rc"; exit "$rc"; fi

log "STATE=VERIFYING"
set +e
python3 kwai_verify_publication.py >>"$REPORT" 2>&1
vrc=$?
set -e
if [ "$vrc" -ne 0 ]; then log "STATE=UNCERTAIN REASON=publication-not-positively-verified"; exit 90; fi
log "STATE=CONFIRMED"
