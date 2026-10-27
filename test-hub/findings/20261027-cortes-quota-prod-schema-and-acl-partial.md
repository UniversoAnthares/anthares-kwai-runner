# CORTES-QUOTA-01 — Neon produção: DDL, grants restritos, rollback e limite de snapshot
STATUS: PARTIAL
AREA: architecture / neon / quota-failover
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40499043365
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40499043365/job/122171785610
COMMIT: 3070afbb257c10e3ed243231861129a06b5b825b
SUPERSEDES: none

## Objetivo
Instalar exclusivamente a persistência de eventos CORTES-QUOTA-01, proteger as permissões de escrita, preservar o ledger de publicações e verificar SQL produtivo sem realizar posts ou alterar fila existente.

## Evidência decisiva
- Neon projeto purple-flower-35918989, branch principal br-crimson-unit-b89nau08. Migração aditiva db/migrations/20261027_cortes_quota_handoff.sql aplicada por transação. Duas tabelas presentes: cortes_quota_handoff_events (18 colunas), cortes_quota_handoff_outbox (14 colunas). Criados índices/constraints definidos na migração. Ledger preexistente mantido.
- SQL QA produtivo dentro de bloco de exceção reversível: uma entrada de evento+outbox foi criada e verificada, colisão de identidade foi rejeitada por unique_violation, evento inexistente na outbox foi rejeitado por foreign_key_violation, e a subtransação foi revertida. Verificação posterior: 0 eventos e 0 entradas de outbox. Nenhuma publicação.
- Papel NOLOGIN cortes_quota_worker_minpriv instalado. Grants somente SELECT/INSERT/UPDATE em tabelas de quota, USAGE/SELECT na sequência outbox e SELECT das colunas target_key,dedupe_key,status,publication_started_at do ledger de publicações. Sem DELETE, INSERT/UPDATE no ledger de publicações, SUPERUSER ou CREATEROLE. Conta atual ara_mcp_reserve_runtime continua herdando papel neondb_owner; não houve alteração de runtime compartilhado.
- Clipper PR #214 integrada ao main; commit 3070afbb257c10e3ed243231861129a06b5b825b; CI #40499043365: 18+8+9+5=40 testes aprovados. Validação do SQL de ACL no Windows também passou (5 testes).
- DB-01: segundo snapshot db01-cortes-quota-postmigration-20261027 foi recusado pelo Neon: HTTP 422 snapshots limit exceeded. Snapshot existente db01-main-manual-20261025 permaneceu intacto. Agendamento automático permanece vazio.

## Limites explícitos
STATUS PARTIAL: falta principal LOGIN exclusivo, configuração protegida de credenciais e integração real de gatilhos/cancelamento ao controlador e ao transporte de fila. Nenhum cancelamento efetivo, publicação ou failover remoto real foi testado. Não remover nem substituir o snapshot existente para contornar limite. O papel ara_mcp_reserve_runtime mantém privilégios herdados amplos; auditar dependentes antes de qualquer redução.

## Próximos critérios de aceitação
1. Identidade autenticada exclusiva com grants de cortes_quota_worker_minpriv; rejeitar membership privilegiada herdada.
2. Detector externo assinado com prova de quota estruturada e autenticação da origem; cancelar somente execução própria, confirmar término, reconciliar recibos.
3. Leitura e envio idempotente ao Neon pela outbox, preservando IDs e payload canônico, com registro remoto verificável.
4. Homologação da restauração de dados e backup externo independente sem exceder a quota.
