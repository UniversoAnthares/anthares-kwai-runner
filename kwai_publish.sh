#!/usr/bin/env bash
set -Eeuo pipefail
REPORT="kwai-publish-status.txt"
: >"$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }

: "${KWAI_VIDEO_URL:?KWAI_VIDEO_URL is required}"
: "${KWAI_VIDEO_TITLE:?KWAI_VIDEO_TITLE is required}"

curl -fL --retry 3 --connect-timeout 15 --max-time 300 -o /tmp/anthares-upload.mp4 "$KWAI_VIDEO_URL"
test -s /tmp/anthares-upload.mp4 || { log "FAIL: empty-video"; exit 80; }
# Basic MP4 signature guard.
head -c 64 /tmp/anthares-upload.mp4 | grep -a -q 'ftyp' || { log "FAIL: invalid-mp4"; exit 81; }
adb shell mkdir -p /sdcard/Movies
adb push /tmp/anthares-upload.mp4 /sdcard/Movies/anthares-upload.mp4 >/dev/null
log "KWAI_VIDEO_STAGED"
python3 kwai_auth_probe.py >>"$REPORT" 2>&1 || { log "FAIL: kwai-not-authenticated"; exit 82; }
python3 kwai_publish_video.py >>"$REPORT" 2>&1 || { rc=$?; log "FAIL: publish-flow-rc=$rc"; exit "$rc"; }
log "KWAI_PUBLISH_FLOW_OK"
# Re-open profile and verify that the title or a newly published UI marker is visible.
adb shell monkey -p com.kwai.video -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
sleep 3
python3 kwai_verify_publication.py >>"$REPORT" 2>&1 || { log "FAIL: publication-not-verified"; exit 83; }
log "KWAI_PUBLICATION_VERIFIED"
