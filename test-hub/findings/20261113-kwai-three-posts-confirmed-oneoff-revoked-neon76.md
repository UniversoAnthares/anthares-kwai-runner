# Kwai: três publicações comprovadas e reconciliadas — produção Neon 76

DATE_UTC: 2026-11-13
RESULT: THREE_CONFIRMED_NO_DUPLICATES_ONEOFF_REVOKED
COST_ADDITIONAL_BRL: 0
ACCOUNT_SCOPE: kwai:lucasrosalem; kwai:universoanthares

## Execução auditável
- [Read-only six-frame proof](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43511361479): três URLs oficiais de perfis corretos, timestamp ~10s após o START canônico, MP4 WordPress contra CDN Kwai, SIFT 6/6 quadros por vídeo. Artefato: kwai-three-public-readback.json. Fonte observada com SHA-256 de arquivo distinto do hash lógico do dispatch; tratada explicitamente como `media_hash_kind=dispatch_identity`.
- OIDC [reconciliation run](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43516677494): revalidação independente dos 3 arquivos e CDN, comparação de hash observado, seis quadros, conta, horário, source URL e status original; CAS de id/status/generation/started/owner/remoteId com autorização exclusiva do workflow. `THREE_KWAI_ROWS_CONFIRMED=YES`, `KWAI_VIDEO_UPLOADS=0`.
- SQL Neon read-only após a execução: os três registros constam `status=confirmed`, `remote_id` preenchido com URL oficial, `confirmation_evidence.kind=kwai_three_public_sift_oidc_reconciled_v1`, `qualifying_distinct_frames=6`, `wp_callback_state=completed`, sem lease ativo. Contagem `started` + `uncertain` para duas contas = 0. A consulta de duplicatas `GROUP BY target_key,remote_id HAVING count(*)>1` retornou [].

| Conta | Segmento | Status anterior | Kwai URL |
|---|---|---|---|
| lucasrosalem | cOhqEaY3-08 1983–2023 | cancelled (erroneously disregarded) | https://www.kwai.com/@lucasrosalem/video/5200963257196327565 |
| lucasrosalem | A7BsgCe3-oo 7595–7635 | uncertain | https://www.kwai.com/@lucasrosalem/video/5236429103303004807 |
| universoanthares | A7BsgCe3-oo 7595–7635 | started, lease expired | https://www.kwai.com/@universoanthares/video/5244028928629526188 |

WordPress reconheceu três callbacks de `completed`, uma vez por registro. Nenhum reenvio ou republicação.

## Encerramento da autorização de risco elevado
- PR #2589 trigger de execução única; workflow `kwai-three-verified-reconcile.yml` recebeu OIDC com permissão restrita.
- PR #2590 retirou `id-token: write`, push/schedule e passou a ser ação manual inerte. Removeu do `infra/neon-cortes-queue/index.mjs` o papel `kwai-oneoff-reconciler` e a rota POST `kwai-oneoff-confirm-public`.
- Código de revogação implantado em QA Neon `cortesqueue` deployment 10 e produção deployment **76**, ambos `completed/active` em 13/11. Sem alteração da configuração de ambiente ou dos registros de publicações durante a revogação.
- O teste `kwai-oneoff-public-reconcile.test.mjs` mantém o resultado histórico verificável e exige role/endpoint OIDC desativados.

## Investigação de isolamento SQL (pendência separada)
- No projeto `anthares-ara-ha`, branch `br-crimson-unit-b89nau08`, a tabela `public.cortes_publications` reportou `relrowsecurity=false`, `relforcerowsecurity=false`, `pg_policies=[]`. Todas as tabelas `cortes_*` consultadas também reportaram RLS desativado.
- Os `information_schema.role_table_grants` de `cortes_publications` listam explicitamente o dono `neondb_owner`; a função `infra/neon-cortes-queue/index.mjs` acessa SQL via `process.env.DATABASE_URL` e endpoint Neon HTTP SQL. O health expõe `network_isolation=false`, `rls_attested=false` e `UNPROVEN_SQL_ROLE_AND_RLS_SCOPE`.
- O dono da tabela normalmente ignora RLS, salvo `FORCE ROW LEVEL SECURITY`; papéis BYPASSRLS também ignoram políticas. Portanto, ativar `ENABLE ROW LEVEL SECURITY` na tabela mantendo a identidade administrativa corrente não comprova isolamento; `FORCE` sem políticas e nova credencial restrita pode derrubar produtores Instagram, Pinterest e LinkedIn que compartilham `cortes_publications`.
- Migração necessária em fases: (a) QA: separar contas funcionais por papéis PostgreSQL sem BYPASSRLS e conceder mínimo de tabelas; (b) políticas `USING` e `WITH CHECK` específicas a `target_key` e operações permitidas; (c) funções Neon com conexões de papel de runtime isolado (uma identidade/credencial por serviço), recusando consulta administrativa; (d) homologar acessos permitidos e negados em QA, com testes de INSERT/SELECT/UPDATE/CAS e triggers; (e) rollout supervisionado em produção com rollback e proteção da fila. **NENHUMA ALTERAÇÃO DE RLS DE PRODUÇÃO EXECUTADA NESTA OPERAÇÃO**. A indicação de isolamento permanece `UNPROVEN`.
- Fontes: https://www.postgresql.org/docs/current/ddl-rowsecurity.html e https://neon.tech/docs/manage/database-access.

## Pendências residuais
- O corte 06h–23h está implantado na função Neon #76, com código e testes; execução real posterior à implantação para ambas as contas ainda precisa ser observada, sem publicar um canário indevido.
- Android cloud independente de PC/celular ainda não está provisionado. `cloud_cutover.enabled=false`. Oracle, CutMotions, propostas pagas e candidaturas sujeitas a resposta externa estão excluídos pela decisão do titular.
- O publicador físico atual não foi desativado. Nenhuma alteração de orçamento/serviço contratado.

Estado verificado: todos os três incidentes de publicações incertas foram resolvidos e o acesso OIDC temporário foi revogado; RLS e hosting Android cloud são bloqueios técnicos distintos.
