# AOI item fixo #16 — LinkedIn personal QA P0 #2043 terminal proof
STATUS: INCIDENT_DONE; AOI_ITEM_16_PARTIAL
ITEMS: [16]
AREA: qa-p0-linkedin-personal-proof-documentation
DATE_UTC: 2026-11-06T15:56:30Z
OWNER: chatgpt-aoi16-linkedin-2043-proof-20261106
LEASE: CLOSED
SUPERSEDES: 20261106-lease-aoi16-linkedin2043-proof-documentation.md
GOVERNANCE_MANIFEST: 223433740e807a90
SOURCE_COMMIT: e0743b074fb287d5382294142e955b1d4510eca1
INCIDENT: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/2043
RUN_68: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42236467314
RUN_69: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42247012171
RUN_69_JOB: 127991766470
COST_ADDED: R$0
NEW_MANUAL_UPLOADS_DURING_AUDIT: 0

## Real evidence of incident closure
- Historical failed #2043 workload stopped at PERSONAL_STAGE=media_readonly, before upload. The code correction was merged in PR #2127.
- Run #68 on 2026-11-06 succeeded on the corrected main branch: media preflight, fenced queue_start, actual LinkedIn upload and API acceptance. It received `urn:li:ugcPost:7524481705588469762`, initially uncertain in Neon.
- LinkedIn public HEAD of `/embed/feed/update/urn:li:ugcPost:7524481705588469762` returned HTTP 200 without redirect; nonexistent-URN negative control HEAD returned HTTP 404.
- Run #69 completed success, log at 15:52:13.653Z `PERSONAL_PUBLIC_READBACK_CONFIRMED=1` with media preflight and upload complete.
- Neon read directly after run #69: `cortes-fanout-linkedin-bd2936ba317cfe15c499d698f8a4f203` changed to `status=confirmed`, `remote_id=urn:li:ugcPost:7524481705588469762`, `confirmation_evidence.kind=linkedin_public_embed_http200`, `updated_at=2026-11-06T15:52:13.613Z`; linkedin:personal confirmed total =117.
- Owner GitHub issue #2043 closed as `completed` at 2026-11-06T15:54:53Z, after terminal proof was recorded in issue comment.

## Independent ongoing publication state
- Run #69 also created another publication with a distinct remote ID `urn:li:ugcPost:7524498950419025920`. Its public LinkedIn HEAD returned HTTP 200, and its Neon record `cortes-fanout-linkedin-f705564c1376ba00ace782c88ea2c3e3` remained `uncertain` at last check, pending normal authenticated public readback. Preserve idempotency; never re-upload it.
- Primary LinkedIn personal remains active as already authorized by owner, standby remains disabled; other social publishers remain unchanged.
- AOI fixed item 16 remains PARTIAL because other independent QA P0 issues, notably #2044 Instagram and #2047 CORTES, still lack post-fix real remote confirmation. The owner's authorization for LinkedIn personal alone does not cover reactivating these publishers.
- Earlier attempt to rerun disabled standby reconciliation-only job got GitHub HTTP 403; DENIED_PENDING_REVIEW remains and is not bypassed.

## Scope and rollback
Documentation and P0 closure only. No new publisher workflow, SQL mutation, duplicate job, fee, credential change or site deployment. Rollback of documentation via PR revert; incident closure has independent original proof in GitHub and Neon.
