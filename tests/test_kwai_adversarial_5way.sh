#!/usr/bin/env bash
set -Eeuo pipefail
CASE="${1:?case required}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$CASE" in
 ready-proof-tamper)
  rm -f /tmp/kwai-publish-ready.json
  printf '%s' '{"job_id":"OTHER","media_name":"m.mp4","media_sha256":"abc","title":"t"}' >/tmp/kwai-publish-ready.json
  set +e
  KWAI_QUEUE_JOB_ID=JOB KWAI_MEDIA_NAME=m.mp4 KWAI_MEDIA_SHA256=abc KWAI_ANDROID_VIDEO=/sdcard/m.mp4 KWAI_VIDEO_TITLE=t python3 "$ROOT/kwai_publish_video.py" commit > /tmp/out 2>&1
  rc=$?; set -e
  test "$rc" = 77; grep -q 'ready-proof-mismatch' /tmp/out; ! grep -q 'STATE=PUBLISH_REQUESTED' /tmp/out
  echo PROVEN_READY_PROOF_TAMPER_FAIL_CLOSED
 ;;
 complete-ack-loss)
  python3 - "$ROOT/kwai_publish.sh" <<'PY'
import pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
a=s.index('kwai_publish_video.py commit')
b=s.index('kwai_queue_state.sh complete')
c=s.index('central-complete-not-acknowledged')
assert a < b < c
block=s[b:c+200]
assert 'STATE=UNCERTAIN' in block
print('PROVEN_COMPLETE_ACK_LOSS_STAYS_UNCERTAIN')
PY
 ;;
 verifier-evidence-loss)
  python3 - "$ROOT/kwai_publish.sh" <<'PY'
import pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
p=s.index('verification-evidence-missing')
pre=s[max(0,p-250):p+300]
assert 'mark_uncertain' in pre
assert 'STATE=UNCERTAIN' in pre
print('PROVEN_VERIFIER_EVIDENCE_LOSS_FAIL_CLOSED')
PY
 ;;
 heartbeat-renew-loss)
  python3 - "$ROOT/kwai_queue_heartbeat.sh" <<'PY'
import pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
assert 'LEASE_HEARTBEAT_FAILED' in s
assert 'kill -TERM "$1"' in s
assert 'STATE=FAILED_SAFE REASON=lease-heartbeat-lost' in s
print('PROVEN_HEARTBEAT_RENEW_LOSS_KILLS_CHILD')
PY
 ;;
 reconcile-no-republish)
  python3 - "$ROOT/kwai_reconcile_uncertain.sh" <<'PY'
import pathlib,sys,re
s=pathlib.Path(sys.argv[1]).read_text()
assert 'kwai_verify_publication.py' in s
assert re.search(r'kwai_queue_state\.sh"? reconcile',s)
assert 'kwai_publish_video.py' not in s
assert 'kwai_publish.sh' not in s
assert 'STATE=PUBLISH_REQUESTED' not in s
print('PROVEN_RECONCILE_OBSERVATION_ONLY')
PY
 ;;
esac
