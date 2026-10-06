# TikTok real canary v2 — UNCERTAIN after Render OOM
STATUS: RECONCILED_ABSENT
DATE: 2026-10-06
AREA: tiktok-publish
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37407210637
JOB: 112087313503

Evidence:
- exact synthetic MP4 generated and validated: H264 1080x1920 30fps + AAC, duration 12.0s, size 69717.
- queue enqueue succeeded for tiktok-canary-20261006-synthetic-v2.
- exact lease acquired, generation 1.
- prepublish session gate passed: bootstrapped=true, identity_verified=true, ready_for_tiktok=true.
- publication_started was crossed before POST /publish.
- POST /publish ended HTTP 502 at 03:09:38Z.
- workflow fail-closed handler emitted CANARY_STATE=UNCERTAIN and central fail with published_possible=true.
- Render event evt-db26csou01pc73d27u1g at 03:09:39Z: server_failed, oomKilled=true, memoryLimit=512Mi.
- Render restarted and became available at 03:10:00Z.
- no positive remote_id/confirmation_evidence was returned to the workflow.
Safety decision: NO RETRY until independent reconciliation proves absence of a new TikTok post. OOM occurred after publication_started, so duplicate risk is real.
Root cause for transport failure: Render free instance exceeded 512Mi during /publish. This is now the infrastructure defect to remove after reconciliation.


## Independent reconciliation
User checked the target TikTok profile universo.anthares after the failed canary and reported that the diagnostic video did not appear. Treat v2 as reconciled absent for retry fencing purposes. Do not reuse v2 dedupe/job id; next attempt must use a fresh identity after the OOM defect is removed.
