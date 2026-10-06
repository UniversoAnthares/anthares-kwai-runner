#!/usr/bin/env bash
set -Eeuo pipefail

OP="${1:?usage: kwai_queue_state.sh started|complete|fail|reconcile [value]}"
VALUE="${2:-}"
CONTROL_URL="${ANTHARES_CONTROL_URL:-https://anthares-control.anthares1.workers.dev}"
EXPECTED_VERSION="${ANTHARES_CONTROL_EXPECTED_VERSION:-2026-10-05-queue-heartbeat-renew-v15}"
: "${KWAI_QUEUE_JOB_ID:?KWAI_QUEUE_JOB_ID is required}"

health="$(curl --fail-with-body -fsS "$CONTROL_URL/health")"
python3 - "$EXPECTED_VERSION" "$health" <<'PY'
import json,sys
expected=sys.argv[1]
d=json.loads(sys.argv[2])
if d.get("version")!=expected:
    raise SystemExit("CONTROL_VERSION_MISMATCH")
if d.get("pc_fallback") is not False:
    raise SystemExit("CONTROL_PC_FALLBACK_NOT_DISABLED")
PY

test -n "${ACTIONS_ID_TOKEN_REQUEST_URL:-}" || { echo 'OIDC_REQUEST_URL_MISSING'; exit 41; }
test -n "${ACTIONS_ID_TOKEN_REQUEST_TOKEN:-}" || { echo 'OIDC_REQUEST_TOKEN_MISSING'; exit 42; }
sep='&'; [[ "$ACTIONS_ID_TOKEN_REQUEST_URL" == *'?'* ]] || sep='?'
aud='https%3A%2F%2Fanthares-control.anthares1.workers.dev'
OIDC_TOKEN="$(curl -fsSL -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "${ACTIONS_ID_TOKEN_REQUEST_URL}${sep}audience=${aud}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["value"])')"
test -n "$OIDC_TOKEN"
echo "::add-mask::$OIDC_TOKEN"

case "$OP" in
  started)
    endpoint='started'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1]},separators=(",",":")))
PY
)"
    ;;
  complete)
    test -n "$VALUE" || { echo 'CONFIRMATION_EVIDENCE_MISSING'; exit 43; }
    endpoint='complete'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$VALUE" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1],"confirmed":True,"confirmation_evidence":sys.argv[2]},separators=(",",":")))
PY
)"
    ;;
  fail)
    endpoint='fail'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$VALUE" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1],"published_possible":True,"error_class":"kwai_publish_uncertain","error_message":sys.argv[2][:400]},separators=(",",":")))
PY
)"
    ;;
  reconcile)
    test -n "$VALUE" || { echo 'RECONCILIATION_EVIDENCE_MISSING'; exit 45; }
    endpoint='reconcile'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$VALUE" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1],"confirmed":True,"remote_id":"kwai:"+sys.argv[1],"confirmation_evidence":sys.argv[2]},separators=(",",":")))
PY
)"
    ;;
  *) echo "UNKNOWN_QUEUE_OP=$OP"; exit 44 ;;
esac

resp="$(curl --fail-with-body -fsS -X POST \
  -H "Authorization: Bearer $OIDC_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "$payload" "$CONTROL_URL/github-queue/$endpoint")"

python3 - "$OP" "$resp" <<'PY'
import json,sys
op=sys.argv[1]; d=json.loads(sys.argv[2])
if d.get("ok") is not True: raise SystemExit("QUEUE_ACK_NOT_OK")
j=d.get("job") or {}
if op=="started" and j.get("publication_started") is not True:
    raise SystemExit("QUEUE_STARTED_FLAG_MISSING")
if op=="complete" and not (j.get("confirmed") is True and j.get("status")=="published"):
    raise SystemExit("QUEUE_COMPLETE_NOT_CONFIRMED")
if op=="fail" and j.get("status")!="uncertain":
    raise SystemExit("QUEUE_FAIL_NOT_UNCERTAIN")
if op=="reconcile" and not (j.get("confirmed") is True and j.get("status")=="published"):
    raise SystemExit("QUEUE_RECONCILE_NOT_CONFIRMED")
PY

echo "STATE=CENTRAL_${OP^^}_ACK"
