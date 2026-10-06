# Control plane v16 fencing and crash recovery proven in production
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: 37396894429
JOB: 112054896540
COMMIT: 4f64b5b027041d5e3e2fcedcefdee15f18d45241
SUPERSEDES: 20261005-lease-control-fencing-crash-recovery-v16.md

## Resultado
PROVEN in production. Worker version 2026-10-05-queue-fencing-v16. Cloudflare Version ID 1a25c85d-aea3-4bc9-8a8b-5fcedef7abcd.

## Evidencia
QUEUE_SELFTEST_HTTP=200.
lease_generation_incremented=true.
stale_generation_start_rejected=true.
stale_generation_complete_rejected=true.
stale_generation_fail_rejected=true.
expired_unstarted_recovered=true.
started_expiry_protected=true.
lease_renew_repeated=true.
single_job_double_claim=true.
KWAI_PRODUCTION_QUEUE_OIDC_SELFTEST_OK.

## Invariante consolidada
Cada nova aquisicao incrementa lease_generation. Mutacoes do holder exigem a geracao atual, impedindo processo obsoleto de started/complete/fail apos reclaim. Job expirado antes de publication_started pode ser recuperado; depois de publication_started expira para uncertain e exige reconciliacao, nunca retry cego.

## Harness
O primeiro push de validacao 37396865276 foi INVALID por indentacao YAML e nao criou jobs. A indentacao foi corrigida; o run valido e 37396894429.
