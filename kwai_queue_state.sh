#!/usr/bin/env bash
set -Eeuo pipefail

# Canonical KW-05 cloud route. Never fall back to legacy Cloudflare authority.
if [ "${KWAI_QUEUE_BACKEND:-}" = "neon" ]; then
  op="${1:?usage: kwai_queue_state.sh started|renew|complete|fail}"
  value="${2:-}"
  : "${KWAI_QUEUE_JOB_ID:?}"
  : "${KWAI_LEASE_GENERATION:?}"
  file="$(mktemp)"
  trap 'rm -f "$file"' EXIT
  case "$op" in
    started|renew|fail)
      python3 - "$file" "$op" "$KWAI_QUEUE_JOB_ID" "$KWAI_LEASE_GENERATION" "$value" <<'PY'
import json,sys
path,op,job,gen,val=sys.argv[1:]
d={'id':job,'lease_generation':int(gen)}
if op=='renew': d['lease_seconds']=int(val or 600)
with open(path,'w',encoding='utf8') as f:json.dump(d,f)
PY
      action="$op"
      [ "$action" = "started" ] && action=start
      python3 tools/cortes_kwai_neon_cloud.py "$action" --json "@$file"
      ;;
    complete)
      : "${KWAI_NEON_ATTESTATION_JSON:?independent attestation required}"
      python3 - "$file" "$KWAI_NEON_ATTESTATION_JSON" "$KWAI_QUEUE_JOB_ID" "$KWAI_LEASE_GENERATION" "${KWAI_MEDIA_SHA256:-}" "$value" <<'PY'
import base64,json,sys
out,source,job,generation,sha,legacy=sys.argv[1:]
with open(source,encoding='utf8') as f: proof=json.load(f)
assert proof.get('account')=='lucasrosalem'
assert proof.get('media_sha256')==sha and len(sha)==64
assert proof.get('verifier_id')=='kwai-independent-account-readback-v1'
assert proof.get('attestation_hmac') and proof.get('public_url') and proof.get('remote_id')
if legacy:
 d=json.loads(base64.urlsafe_b64decode(legacy+'='*(-len(legacy)%4)))
 assert d.get('job_id')==job and d.get('media_sha256')==sha
 with open(out,'w',encoding='utf8') as f:
  json.dump({'id':job,'lease_generation':int(generation),
             'remote_id':proof['remote_id'],'confirmation_evidence':proof},f)
PY
      python3 tools/cortes_kwai_neon_cloud.py confirm --json "@$file"
      ;;
    reconcile) echo KWAI_NEON_RECONCILIATION_REQUIRES_EXTERNAL_READBACK >&2; exit 90 ;;
    *) echo KWAI_NEON_QUEUE_OP_INVALID >&2; exit 44 ;;
  esac
  echo "STATE=CENTRAL_${op^^}_ACK"
  exit 0
fi
# All publication-capable consumers of the legacy queue are retired.
if [ "${KWAI_KW05_LEGACY_PUBLISH_DISABLED:-1}" = "1" ]; then
  echo KWAI_LEGACY_CLOUDFLARE_QUEUE_DISABLED >&2
  exit 91
fi


OP="${1:?usage: kwai_queue_state.sh started|complete|fail|reconcile|renew [value]}"
VALUE="${2:-}"
CONTROL_URL="${ANTHARES_CONTROL_URL:-https://anthares-control.anthares1.workers.dev}"
EXPECTED_VERSION="${ANTHARES_CONTROL_EXPECTED_VERSION:-2026-10-17-physical-android-v18}"
: "${KWAI_QUEUE_JOB_ID:?KWAI_QUEUE_JOB_ID is required}"

case "$OP" in
  started|complete|fail|renew)
    : "${KWAI_LEASE_GENERATION:?KWAI_LEASE_GENERATION is required for fenced holder mutations}"
    ;;
esac

health="$(curl --fail-with-body -fsS "$CONTROL_URL/health")"
python3 - "$EXPECTED_VERSION" "$health" <<'PY'
import json,sys
d=json.loads(sys.argv[2])
if d.get("version")!=sys.argv[1]: raise SystemExit("CONTROL_VERSION_MISMATCH")
if d.get("pc_fallback") is not False: raise SystemExit("CONTROL_PC_FALLBACK_NOT_DISABLED")
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
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$KWAI_LEASE_GENERATION" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1],"lease_generation":int(sys.argv[2])},separators=(",",":")))
PY
)"
    ;;
  complete)
    test -n "$VALUE" || { echo 'CONFIRMATION_EVIDENCE_MISSING'; exit 43; }
    : "${KWAI_REMOTE_POST_ID:?KWAI_REMOTE_POST_ID must come from observed Kwai post}"
    : "${KWAI_PUBLIC_POST_URL:?KWAI_PUBLIC_POST_URL must be an observed public Kwai URL}"
    python3 -m anthares_publisher.public_verify --url "$KWAI_PUBLIC_POST_URL" --post-id "$KWAI_REMOTE_POST_ID" --account "${KWAI_EXPECTED_ACCOUNT:-lucasrosalem}" >/dev/null || { echo 'KWAI_PUBLIC_URL_NOT_INDEPENDENTLY_REACHABLE'; exit 46; }
    endpoint='complete'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$VALUE" "$KWAI_LEASE_GENERATION" "$KWAI_REMOTE_POST_ID" "$KWAI_PUBLIC_POST_URL" "${KWAI_EXPECTED_ACCOUNT:-lucasrosalem}" <<'PY'
import json,sys
from anthares_publisher.contract import PublicationEvidence,validate_evidence
job,evidence,generation,remote,url,account=sys.argv[1:]
if remote in (job,"kwai:"+job) or len(remote)<6:
    raise SystemExit("REMOTE_POST_ID_NOT_INDEPENDENT")
validate_evidence(PublicationEvidence("kwai",account,remote,url),"kwai",account)
print(json.dumps({"id":job,"confirmed":True,"confirmation_evidence":evidence,"lease_generation":int(generation),"remote_id":remote,"public_url":url},separators=(",",":")))
PY
)"
    ;;
  fail)
    endpoint='fail'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$VALUE" "$KWAI_LEASE_GENERATION" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1],"published_possible":True,"error_class":"kwai_publish_uncertain","error_message":sys.argv[2][:400],"lease_generation":int(sys.argv[3])},separators=(",",":")))
PY
)"
    ;;
  renew)
    endpoint='renew'
    ttl="${VALUE:-600}"
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$KWAI_LEASE_GENERATION" "$ttl" <<'PY'
import json,sys
print(json.dumps({"id":sys.argv[1],"lease_generation":int(sys.argv[2]),"ttl_seconds":int(sys.argv[3])},separators=(",",":")))
PY
)"
    ;;
  reconcile)
    test -n "$VALUE" || { echo 'RECONCILIATION_EVIDENCE_MISSING'; exit 45; }
    # A queue job ID is NOT a Kwai post ID. Never synthesize remote identity.
    : "${KWAI_REMOTE_POST_ID:?KWAI_REMOTE_POST_ID must be independently observed before reconciliation}"
    : "${KWAI_PUBLIC_POST_URL:?KWAI_PUBLIC_POST_URL must be independently observed before reconciliation}"
    python3 -m anthares_publisher.public_verify --url "$KWAI_PUBLIC_POST_URL" --post-id "$KWAI_REMOTE_POST_ID" --account "${KWAI_EXPECTED_ACCOUNT:-lucasrosalem}" >/dev/null || { echo 'KWAI_PUBLIC_URL_NOT_INDEPENDENTLY_REACHABLE'; exit 46; }
    endpoint='reconcile'
    payload="$(python3 - "$KWAI_QUEUE_JOB_ID" "$VALUE" "$KWAI_REMOTE_POST_ID" "$KWAI_PUBLIC_POST_URL" "${KWAI_EXPECTED_ACCOUNT:-lucasrosalem}" <<'PY'
import json,re,sys
from anthares_publisher.contract import PublicationEvidence,validate_evidence
job,evidence,remote,url,account=sys.argv[1:]
if len(remote)<6 or remote in (job,"kwai:"+job) or not re.fullmatch(r"[A-Za-z0-9_:/?&.=%-]+",remote):
    raise SystemExit("RECONCILIATION_REMOTE_ID_INVALID")
validate_evidence(PublicationEvidence("kwai",account,remote,url),"kwai",account)
print(json.dumps({"id":job,"confirmed":True,"remote_id":remote,"public_url":url,"confirmation_evidence":evidence},separators=(",",":")))
PY
)"
    ;;
  *) echo "UNKNOWN_QUEUE_OP=$OP"; exit 44 ;;
esac

resp="$(curl --fail-with-body -fsS -X POST -H "Authorization: Bearer $OIDC_TOKEN" -H 'Content-Type: application/json' --data "$payload" "$CONTROL_URL/github-queue/$endpoint")"

python3 - "$OP" "$resp" <<'PY'
import json,sys
op=sys.argv[1]; d=json.loads(sys.argv[2])
if d.get("ok") is not True: raise SystemExit("QUEUE_ACK_NOT_OK")
j=d.get("job") or {}
if op=="renew" and int(j.get("lease_generation",-1)) < 1: raise SystemExit("QUEUE_RENEW_GENERATION_MISSING")
if op=="started" and j.get("publication_started") is not True: raise SystemExit("QUEUE_STARTED_FLAG_MISSING")
if op=="complete" and not (j.get("confirmed") is True and j.get("status")=="published"): raise SystemExit("QUEUE_COMPLETE_NOT_CONFIRMED")
if op=="fail" and j.get("status")!="uncertain": raise SystemExit("QUEUE_FAIL_NOT_UNCERTAIN")
if op=="reconcile" and not (j.get("confirmed") is True and j.get("status")=="published"): raise SystemExit("QUEUE_RECONCILE_NOT_CONFIRMED")
PY

echo "STATE=CENTRAL_${OP^^}_ACK"
