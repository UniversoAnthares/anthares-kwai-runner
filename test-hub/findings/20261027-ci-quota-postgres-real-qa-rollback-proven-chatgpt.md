# CI quota fenced ledger — PostgreSQL QA rollback proof
STATUS: PROVEN
AREA: architecture / ci-quota-ledger
DATE: 2026-10-27
RUN: Neon SQL connector, isolated QA branch
JOB: br-silent-mud-b8fzvqta
COMMIT: 50128a042e7adf6c986701321454e6bdf7af070f
SUPERSEDES: none

## Objetivo
Verificar em um PostgreSQL Neon real a migration versionada em db/migrations/20261027_ci_quota_fenced_ledger.sql sem tocar na produção ou deixar tabelas de teste.

## Evidência
Projeto: purple-flower-35918989. QA branch: br-silent-mud-b8fzvqta. Consulta inicial ao catálogo confirmou ausência da tabela public.anthares_ci_quota_attempts. Um bloco SQL DO com subtransação abortada propositalmente criou a tabela e seu índice, aplicou REVOKE FROM PUBLIC, testou INSERT único, conflito ON CONFLICT DO NOTHING, rejeição de token de proprietário diferente, incremento de lease_generation de 1 para 2 e rejeição de atualização stale. Todos os asserts SQL passaram. A exceção sentinela EXPECTED_QA_ROLLBACK foi capturada e revertida pelo bloco interno. Consulta posterior ao information_schema confirmou table_persisted_after_rollback=false.

## Resultado
PASS: teste PostgreSQL real, transação reversível, zero resíduo persistente. SQL de migração continua versionado, sem deploy produtivo ou grants novos.

## Limites
Este teste usa uma conexão/um processo e verifica CAS SQL e unicidade. Ainda faltam testes concorrentes com dois hosts, cancelamento e status por APIs reais, vínculo com principal mínimo autenticado e integração ao despachante, sem liberar publicadores automaticamente.
