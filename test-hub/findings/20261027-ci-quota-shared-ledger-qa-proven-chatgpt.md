# CI quota shared PostgreSQL ledger — independent QA
STATUS: PROVEN
AREA: github / ci-quota-ledger
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504599465
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504599465/job/122190571791
COMMIT: ff68d2c01bb77ccde522bff47d324893afdccf14
SUPERSEDES: test-hub/findings/lease-20261027-ci-quota-shared-ledger-chatgpt.md

## Escopo
Foi implementada camada opt-in SharedQuotaLedger com INSERT de reivindicação única, token de proprietário, geração incrementada por compare-and-swap, lease limitado e histórico JSONB. A tentativa não é retomada automaticamente quando a posse expira; cancelamento remoto e publicação continuam dependentes de evidência terminal e reconciliação independente. A migração SQL permanece APENAS versionada, sem aplicação produtiva.

## Prova
Windows ARA job independente: 6 testes PASS; py_compile PASS; TEMP_CLEANED=True. GitHub hospedado run 40504599465 / job 122190571791: Ran 6 tests in 0.001s; OK; CI_QUOTA_LEDGER_QA=PASS.

## Limites
QA em memória e SQL estático. Não comprova operação real Neon com múltiplos hosts, cancelamento API, integração automática com adaptadores, publicação ou failover externo. Sem alteração de banco, credenciais, workloads sociais ou workflows compartilhados.

## Consequência
Pode integrar código opt-in com revisão normal. Para promover a produção: aplicar migration controlada, principal mínimo, callbacks reais e provas de cancelamento terminal e recibo. Nenhum status de plataforma foi alterado para READY.
