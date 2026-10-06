# Kwai publisher heartbeat wrapper contract proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: 37397505057
JOB: 112056875462
COMMIT: 2eacd85742193178f02e7ea2b5fdb69744eb6540
SUPERSEDES: test-hub/findings/20261005-lease-kwai-publish-heartbeat-integration.md

## Resultado
Reusable fenced heartbeat wrapper is PROVEN by isolated GitHub contract test. It renews the active KWAI_LEASE_GENERATION periodically and fails closed by terminating the child if renew fails.

## Evidencia
bash syntax validation passed.
Normal long-running child produced renew with job id and generation.
Forced renew failure returned 49 and STATE=FAILED_SAFE REASON=lease-heartbeat-lost.
KWAI_HEARTBEAT_CONTRACT_OK.

## Incidente fechado
Run 37397420475 exposed a normal-exit/SIGTERM race in the first wrapper version. Commit 2eacd85742193178f02e7ea2b5fdb69744eb6540 distinguishes intentional helper shutdown from lease loss; rerun passed.

## Limite
No media publication or Android session was used. Wiring this wrapper around the actual long-running publication command remains a separate mutation of the media publisher and must respect its active lease.
