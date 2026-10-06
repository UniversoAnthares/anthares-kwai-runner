# Queue lease renewal + single-job double-claim PROVEN in production v14
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394732038
JOB: 112047887652
COMMIT: 682eb8f81395e8fa8aecbb7b7a9f49d984a9d5c4
SUPERSEDES: 2026-10-05-lease-queue-renew-and-single-job-double-claim.md

## Objetivo
Fechar as lacunas de renovação explícita do lease e prova de claim atômico sobre exatamente um job, preservando os invariantes do control plane.

## Resultado
PROVEN EM PRODUÇÃO no Worker v14. Deploy Cloudflare Version ID 21f1cd93-9a62-426e-a2b4-7602de30355e. O endpoint autenticado /queue-self-test retornou HTTP 200.

## Evidência decisiva
Run 37394732038 / job 112047887652:
- version=2026-10-05-queue-lease-renew-v14
- single_job_double_claim=true
- lease_renew_owner_only=true
- lease_renew_extended=true
- lease_renew_invalid_state_rejected=true
- lease_renew_expired_rejected=true
- failure_counter_reset=true
- KWAI_PRODUCTION_QUEUE_OIDC_SELFTEST_OK

O primeiro run v13, 37394632606, alcançou os novos testes e depois revelou uma inconsistência anterior: recordSuccess zerava failures/consecutive_failures sem limpar disabled_until. A correção v14 limpa disabled_until após sucesso confirmado e o self-test integral passou.

## Consequência
Renovação de lease e exclusão mútua de claim de um único job deixam de ser lacunas. Clientes long-running podem usar /job/renew, /github-queue/renew ou queue_op=renew. Preservar autenticação por owner, estado leased e rejeição de lease expirado. Não reabrir o bug de circuit breaker: sucesso confirmado deve limpar disabled_until.
