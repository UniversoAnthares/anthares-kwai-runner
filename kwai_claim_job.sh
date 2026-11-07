#!/usr/bin/env bash
set -Eeuo pipefail
CONTROL="${ANTHARES_CONTROL_URL:-https://anthares-control.anthares1.workers.dev}"
TTL="${KWAI_LEASE_TTL_SECONDS:-600}"
: "${ACTIONS_ID_TOKEN_REQUEST_URL:?ACTIONS_ID_TOKEN_REQUEST_URL is required}"
: "${ACTIONS_ID_TOKEN_REQUEST_TOKEN:?ACTIONS_ID_TOKEN_REQUEST_TOKEN is required}"
health="$(curl -fsS "$CONTROL/health")"
python3 - "$health" <<'PY'
import json,sys
d=json.loads(sys.argv[1]); assert d.get("version")=="2026-10-17-physical-android-v18",d; assert d.get("pc_fallback") is False,d
PY
sep='&'; [[ "$ACTIONS_ID_TOKEN_REQUEST_URL" == *'?'* ]] || sep='?'
aud='https%3A%2F%2Fanthares-control.anthares1.workers.dev'
jwt="$(curl -fsSL -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "${ACTIONS_ID_TOKEN_REQUEST_URL}${sep}audience=${aud}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["value"])')"
out="$(curl --fail-with-body -fsS -H "Authorization: Bearer $jwt" "$CONTROL/github-queue-get/lease?platform=kwai&ttl_seconds=$TTL")"
python3 - "$out" "${GITHUB_ENV:-}" <<'PY'
import json,sys
d=json.loads(sys.argv[1]); env=sys.argv[2]; assert d.get("ok") is True,d; j=d.get("job")
if not j: print("KWAI_QUEUE_EMPTY"); raise SystemExit(3)
required=["id","lease_generation","source_id","source_start","source_end"]; missing=[k for k in required if j.get(k) in (None,"")]
if missing: raise SystemExit("LEASE_JOB_MISSING="+",".join(missing))
if int(j["lease_generation"])<1 or float(j["source_end"])<=float(j["source_start"]): raise SystemExit("LEASE_CONTRACT_INVALID")
pairs={"KWAI_QUEUE_JOB_ID":j["id"],"KWAI_LEASE_GENERATION":j["lease_generation"],"KWAI_SOURCE_ID":j["source_id"],"KWAI_SOURCE_START":j["source_start"],"KWAI_SOURCE_END":j["source_end"]}
for src,dst in [("video_url","KWAI_VIDEO_URL"),("video_title","KWAI_VIDEO_TITLE"),("expected_account","KWAI_EXPECTED_ACCOUNT")]:
 if j.get(src) not in (None,""): pairs[dst]=j[src]
# A dispatch identity may be SHA-shaped but is NOT a cryptographic media checksum.
# Prefer the actual content checksum delivered by the queue, when present.
content_sha=j.get("content_sha256") or j.get("media_content_sha256")
if not content_sha and j.get("media_hash_kind")!="dispatch_identity":
 content_sha=j.get("media_sha256")
if content_sha:
 import re
 if not re.fullmatch(r"[a-fA-F0-9]{64}",str(content_sha)):
  raise SystemExit("LEASE_MEDIA_CONTENT_SHA_INVALID")
 pairs["KWAI_EXPECTED_MEDIA_SHA256"]=str(content_sha).lower()
if env:
 with open(env,"a") as f:
  for k,v in pairs.items(): f.write(f"{k}={v}\n")
print(json.dumps({"ok":True,"job_id":j["id"],"lease_generation":int(j["lease_generation"])},separators=(",",":"))); print("KWAI_QUEUE_CLAIM_READY")
PY
