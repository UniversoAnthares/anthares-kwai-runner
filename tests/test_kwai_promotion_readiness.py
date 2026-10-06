#!/usr/bin/env python3
import pathlib,re,sys
root=pathlib.Path(__file__).resolve().parents[1]
wf=(root/".github/workflows/kwai-real-publish.yml").read_text()
pub=(root/"kwai_publish.sh").read_text()
checks={
"auth-gate": "Type YES only after kwai-login reports READY" in wf,
"production-still-guarded": "Real publication remains gated until the kwai-publish acceptance workflow is promoted." in wf and "kwai_publish.sh" not in wf,
"canonical-interval": all(x in wf for x in ["source_id","source_start","source_end","KWAI_CANONICAL_INTERVAL_GATE_OK"]),
"publisher-fencing": all(x in pub for x in ["KWAI_LEASE_GENERATION","kwai_queue_heartbeat.sh","kwai_queue_state.sh started"]),
"uncertain-path": "STATE=UNCERTAIN" in pub and "kwai_queue_state.sh fail" in pub,
}
bad=[k for k,v in checks.items() if not v]
print(checks)
if bad: print("PROMOTION_READINESS_FAILED",bad);sys.exit(1)
print("KWAI_PROMOTION_READINESS_STATIC_OK")
