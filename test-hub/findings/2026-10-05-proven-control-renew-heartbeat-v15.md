# Control plane v15: repeated lease heartbeat proven in production
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: 37395158585
JOB: 112049276852
COMMIT: 81c10a1021675fd1b615f8db9cec97c385ee839a
SUPERSEDES: 2026-10-05-lease-control-renew-heartbeat-contract.md

## Objetivo
Provar em producao que o renew do lease suporta heartbeat periodico repetido e preserva as invariantes fail-closed.

## Resultado
PROVEN. Worker em producao: 2026-10-05-queue-heartbeat-renew-v15. Cloudflare Version ID ad065abd-fc61-4e8a-84ff-8b0dcc56f42d. O self-test autenticado via GitHub OIDC terminou HTTP 200.

## Evidencia decisiva
QUEUE_SELFTEST_HTTP=200.
lease_renew_owner_only=true.
lease_renew_extended=true.
lease_renew_repeated=true.
lease_renew_invalid_state_rejected=true.
lease_renew_expired_rejected=true.
single_job_double_claim=true.
KWAI_PRODUCTION_QUEUE_OIDC_SELFTEST_OK.

## Consequencia
O contrato central de heartbeat/renew repetido esta comprovado. O proximo gap e integrar renew no cliente/executor de longa duracao, somente quando a area do publicador correspondente estiver sem lease conflitante.
