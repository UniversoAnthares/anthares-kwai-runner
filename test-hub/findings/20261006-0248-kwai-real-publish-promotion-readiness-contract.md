# Kwai real-publish promotion readiness contract
STATUS: PARTIAL
AREA: kwai-publish
DATE: 2026-10-06
DEPENDS_ON: independent kwai-login/session READY
DO_NOT_PROMOTE_YET: true

The production workflow promotion gap remains intentional until login/session readiness is independently PROVEN.

Promotion acceptance contract, prepared now:
1. consume a canonical queued job carrying source_id/source_start/source_end;
2. require KWAI_QUEUE_JOB_ID and current KWAI_LEASE_GENERATION;
3. run canonical temporal + SHA dedupe before media preparation;
4. invoke kwai_publish.sh only after authenticated expected-account READY;
5. retain heartbeat fencing through prepare -> /started ACK -> commit -> verification -> complete/fail;
6. any failure after /started remains UNCERTAIN and is observation-only on restart;
7. no UNCERTAIN job may be reclaimed into the publisher without strong absence proof;
8. real canary is one job only and must preserve the exact-account verification contract.

This finding advances the integration work without enabling an irreversible path while the external authentication prerequisite is unresolved. Once kwai-login records READY, promotion can be implemented against this checklist instead of rediscovering the wiring.
