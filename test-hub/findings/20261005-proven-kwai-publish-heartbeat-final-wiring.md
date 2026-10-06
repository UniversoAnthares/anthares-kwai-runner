# Kwai publisher final fenced heartbeat wiring proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: 37400963267
JOB: 112067807899
COMMIT: a118c11ca03b22941f0894828c3104c0b75d5f68
SUPERSEDES: test-hub/findings/20261005-lease-kwai-publish-heartbeat-final-wiring.md
LEASE_AREA: kwai-publish
LEASE_CLOSED: 2026-10-06T01:49:00Z

## Resultado
The real kwai_publish.sh entrypoint now requires KWAI_LEASE_GENERATION and self-wraps under kwai_queue_heartbeat.sh before media preparation. The heartbeat therefore covers download, Android staging, prepare, started, commit, verification and complete/fail lifecycle.

## Provas
Run 37400963267 / job 112067807899: KWAI_HEARTBEAT_CONTRACT_OK and KWAI_PUBLISH_HEARTBEAT_WIRING_OK.
Normal child execution renews successfully; forced renew failure terminates fail-closed.
No wrapper recursion; heartbeat begins before REPORT/media preparation.

Control regression: run 37401034918 / job 112068028605 passed production v16 OIDC self-test HTTP 200 with double-claim, repeated renew, generation increment, stale-generation rejection, crash/recovery, reconciliation and circuit breaker flags all true.

## Limite de validade
No real Kwai media Publish was performed. This proves queue/control/publisher wiring and fail-closed behavior; authenticated Android publication remains gated by the independent kwai-login/session readiness.
