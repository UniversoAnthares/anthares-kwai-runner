#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp "$ROOT/kwai_publish.sh" "$TMP/"
cd "$TMP"
printf '000000000000000000000000ftypisom' > video.mp4

cat > curl <<'SH'
#!/usr/bin/env bash
out=''; while [ "$#" -gt 0 ]; do [ "$1" = "-o" ] && { out="$2"; shift 2; continue; }; shift; done
cp video.mp4 "$out"
SH
cat > adb <<'SH'
#!/usr/bin/env bash
case "$*" in
 *"stat -c"*) stat -c %s video.mp4;;
 *"content query"*) echo "Row: 0 _display_name=$KWAI_MEDIA_NAME, _size=$(stat -c %s video.mp4)";;
 *) :;;
esac
SH
cat > kwai_auth_probe.py <<'PY'
print("STATE=READY ACCOUNT=expected")
PY
cat > kwai_verify_publication.py <<'PY'
import os,sys
if os.environ.get("VERIFY_FAIL")=="1": sys.exit(9)
print("KWAI_CONFIRMATION_EVIDENCE=account-title-proof")
PY
cat > kwai_publish_video.py <<'PY'
import os,sys
p=sys.argv[1]; open("events","a").write(p+"\n")
if p=="prepare":
 print("STATE=READY_TO_PUBLISH"); sys.exit(0)
if os.environ.get("COMMIT_FAIL")=="1": sys.exit(8)
print("STATE=PUBLISH_REQUESTED"); sys.exit(0)
PY
cat > kwai_queue_state.sh <<'SH'
#!/usr/bin/env bash
echo "queue:$1" >> events
if [ "$1" = started ] && [ "${STARTED_FAIL:-0}" = 1 ]; then exit 7; fi
exit 0
SH
cat > kwai_queue_heartbeat.sh <<'SH'
#!/usr/bin/env bash
exec "$@"
SH
chmod +x curl adb kwai_queue_state.sh kwai_queue_heartbeat.sh
export PATH="$TMP:$PATH"
base=(env KWAI_HEARTBEAT_ACTIVE=1 KWAI_LEASE_GENERATION=3 KWAI_QUEUE_JOB_ID=job1 KWAI_VIDEO_URL=http://fixture KWAI_VIDEO_TITLE=title KWAI_EXPECTED_ACCOUNT=expected)

run_case(){
 rm -f events kwai-publish-status.txt
 set +e; "$@" >/dev/null 2>&1; rc=$?; set -e
}

run_case env STARTED_FAIL=1 "${base[@]}" bash kwai_publish.sh
test "$rc" = 86
test "$(cat events)" = $'prepare\nqueue:started'

run_case env COMMIT_FAIL=1 "${base[@]}" bash kwai_publish.sh
test "$rc" = 90
test "$(cat events)" = $'prepare\nqueue:started\ncommit\nqueue:fail'

run_case "${base[@]}" bash kwai_publish.sh
test "$rc" = 0
test "$(cat events)" = $'prepare\nqueue:started\ncommit\nqueue:complete'

python3 - <<'PY'
from pathlib import Path
s=Path("kwai_publish.sh").read_text()
assert s.index("kwai_queue_state.sh started") < s.index("kwai_publish_video.py commit")
PY
echo KWAI_STARTED_COMMIT_EXECUTABLE_OK
