# Quota cancellation — Anthares CI (v1)

Effective rule: `CANCELAR_IMEDIATAMENTE_POR_COTA_V1`.

When an owned job or execution stops because of a **confirmed** provider quota, usage or credit limit, the controller must immediately request cancellation of that exact remote job, even if an alternative provider is available. The original execution must not remain waiting for quota reset.

Before a fallback: verify remote terminal status (canceled/failed/terminated/expired) and revoke the original execution lease. For any side-effectful task (publishing, purchases, writes), obtain `NOT_APPLIED` reconciliation. Only then enqueue a **new** idempotent attempt with an eligible standby on a demonstrably independent quota scope.

If cancellation or submission is uncertain: fail closed, retain the task in the safe queue and reconcile; never retry blindly, dispatch in parallel, charge a paid plan, weaken authentication or treat a credential denial as quota.

Code: `tools/ci_quota_cancel_first.py`; tests: `tests/test_ci_quota_cancel_first.py`. The SQLite implementation is **single-host only** and its callbacks have no credentials. Production multi-cloud execution needs a shared transactional lease/fencing ledger and provider-specific cancel, status and enqueue callbacks. The router declares this contract but automatic cancellation is **not yet integrated** into every provider. Never mark a provider operational without real cancellation evidence.

Provider requirements: GitLab pipeline cancellation and status APIs; GitHub Actions run cancellation and status APIs; AppVeyor and Bitrise own provider cancellation APIs; Cloudflare Workers Builds and other platform-specific jobs need separate adapters. No exception for Northflank jobs, browser tasks, social publishers, SMTP or AI: each must either support confirmed cancellation and safe independent failover or stop fail-closed with `CANCEL_UNCONFIRMED` or `CANCELLED_NO_INDEPENDENT_RESERVE`.

Existing CI priority order is unchanged. AppVeyor remains penultimate and GitLab CI last; blocked providers cannot be promoted without a fresh successful run and quota proof. This document is an implementation requirement, **not** proof every platform's adapter is live.

## Shared transactional ledger (2026-10-27)

An **opt-in**, cross-host PostgreSQL ledger implementation now exists in `tools/ci_quota_neon_ledger.py`; its additive schema is versioned in `db/migrations/20261027_ci_quota_fenced_ledger.sql`, with unit tests in `tests/test_ci_quota_neon_ledger.py`. It provides atomic first claim, per-owner token, generation-based compare-and-swap, bounded lease and fail-closed rejection of stale updates. An expired attempt cannot be reclaimed automatically; independent remote-status and side-effect reconciliation remain mandatory.

QA evidence: GitHub Actions run [40504599465](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40504599465) passed 6 tests and printed `CI_QUOTA_LEDGER_QA=PASS`. A separate rollback-only Neon QA transaction validated real PostgreSQL constraints and fencing semantics, then verified the table was absent after rollback (see `test-hub/findings/20261027-ci-quota-postgres-real-qa-rollback-proven-chatgpt.md`).

**Current production status (2026-10-27):** This schema IS deployed on Neon main (project purple-flower-35918989), under the SQL-created restricted `anthares_ci_quota_limited` role. Vercel `anthares-ci-quota-controller` is live with OIDC and `ledger=READY`. GitLab quota handoff to independent GitHub CI is operational for one observed real incident: pipeline 2994547840 -> GitHub run 40510154187 SUCCESS, Neon `FALLBACK_CONFIRMED`.

**External providers:** PR #1557 installed a separate 15-minute GitHub Actions watcher for AppVeyor/Bitrise with an exact account/project/commit check, structured quota evidence, cross-host Neon exclusive claim, provider cancellation/status API, and fail-closed reconciliation. Deployment READY; however, provider API credentials and app/project variables remain unconfirmed. No real AppVeyor/Bitrise quota incident has been observed or canceled. The existing GitHub Actions own-run callback is also not yet universally wired. A green deployment alone is not evidence of remote cancellation; see `test-hub/findings/20261027-appveyor-bitrise-quota-watcher-implemented-auth-pending.md`.

## Anthares Remote standby instalado — 2026-10-27

Além do watcher GitHub OIDC, existe um segundo executor independente no Windows `DESKTOP-FTDK0HP`, tarefa SYSTEM `Anthares CI Quota Cancel Standby` a cada 15 minutos. O script versionado `anthares-remote-agent/windows/ci-quota-cancel-standby.ps1` usa chave privada RSA-3072 local criptografada via DPAPI; o Vercel valida somente a chave pública `ANTHARES_REMOTE_QUOTA_PUBJWK`. Os dois executores compartilham a reserva atômica/fencing da tabela produtiva Neon `public.anthares_ci_quota_attempts`. O diagnóstico de produção retornou `READY_RSA_NEON` (assinatura remota válida + banco de dados com papel restrito), sem cota sintética.

**Atenção: não confundir controle instalado com cancelamento de provedor comprovado.** No fechamento, tanto GitHub quanto Anthares Remote não possuíam as credenciais e os identificadores exatos de AppVeyor/Bitrise; o estado é `NOT_CONFIGURED`. A reserva permanece instalada e falha em modo fechado, sem cancelar sem prova nem tentar outra execução. Não foi observado um evento real novo desses provedores. Evidência completa: `test-hub/findings/20261027-ara-quota-standby-rsa-production-auth-live-partial.md`.

## Harness CI — homologação de contrato e limitações (2026-10-27)

- Pipeline Harness #908: SUCCESS em 58s; prova executor CI, não prova cancelamento.
- Adaptador HarnessPipelineRun (PR #1590), wrapper de SharedQuotaLedger (PR #1606) e preflight GET do UUID+pipeline antes do PUT AbortAll com polling limitado (PR #1619). Correção global: HTTP 403 não comprova quota.
- Teste efetivamente executado: Anthares Remote, Python 3.12, fontes oficiais da branch carregadas em memória sem escrita local; 24 testes aprovados, 0 falhas e 0 erros. Provas incluem ordem GET/PUT/GET, concorrência, fencing CAS, execução estrangeira, cancelamento incerto, reconciliação e expiração de lease. API Harness e PostgreSQL foram SIMULADOS nesses testes.
- Endpoints confirmados pela documentação oficial: PUT /pipeline/api/pipeline/execute/interrupt/{planExecutionId} com interruptType=AbortAll e GET /pipeline/api/pipelines/execution/v2/{planExecutionId}; exigem x-api-key. GET da execução #908 sem credencial respondeu HTTP 401, o que não valida token.
- Consulta read-only ao Neon real: projeto purple-flower-35918989, banco neondb, tabela public.anthares_ci_quota_attempts, 8 colunas e 3 registros existentes. Não foram criados registros de teste em produção.
- Limitação crítica: controlador Vercel provider-cancel aceita somente appveyor/bitrise; não há despachante ativo para Harness nem x-api-key autenticada comprovada. A ferramenta de controle remoto negou acesso ao token DPAPI; não contornar a negação. Manter eligible=false e ci_eligible=false.

## Harness — controlador externo pronto em código, publicação bloqueada por cota

PR #1625 integrou a aceitação de claims/reports Harness ao mesmo controller Vercel/Neon de AppVeyor/Bitrise. Validado 2026-10-27 com 5 testes Node.js em memória (OIDC/Neon simulados), 0 falhas. Esse suporte é passivo: NÃO cancela builds automaticamente e não autentica a API Harness por si só.

Tentativa de publicar no projeto de produção Vercel anthares-ci-quota-controller (team_0LJFNVrGdH5dvDqnTEN3FFoT) retornou HTTP 402 payment_required, recurso api-deployments-free-per-day (mais de 100 implantações gratuitas diárias), retryAfter=86400 segundos. Nenhum deployment novo foi criado. Não repetir em janela bloqueada, não contratar plano e não presumir redundância operacional externa. A produção permanece no deployment dpl_DwZ1X8MLS9ZAhUDnyJezg4dEmEmu sem a permissão Harness. Após cota restaurada, publicar exatamente oito arquivos de deploy/anthares-ci-quota-controller/ da main, verificar health e claims Harness sob autenticador legítimo e só então atualizar o estado produtivo. A credencial Harness x-api-key e a operação real de AbortAll continuam sem comprovação; elegibilidade permanece falsa.

## Harness CI — execução real da nova suíte (2026-10-27)

PR #1627 incluiu etapa real de testes do cancel-first no pipeline Git-backed do Harness (4 módulos Python com 24 testes e teste Node opcional de 5 casos). A integração GitHub/Harness acionou a execução kbHfz70fTUiuYNoGx-QoBA no commit 66aef1245c04ebd16e0e4e4db593440a2604cc03. GitHub commit status, contexto Build_and_Test, retornou state=success, descrição Stage - Build and Test is SUCCEEDED, updated_at=2026-10-27T18:51:55Z. URL: https://app.harness.io/ng/account/xAEBvmMUTjql7g2Exxmp-g/ci/orgs/default/projects/default_project/pipelines/pipeline_UniversoAnthares_anthares_kwai_runner_build_9a3d/executions/kbHfz70fTUiuYNoGx-QoBA/pipeline. O estágio concluiu; logs individuais não foram inspecionados via API autenticada. Não interpretar esse sucesso como autenticação do x-api-key do controlador, cancelamento real nem deploy da versão nova no Vercel.


## Harness cancel-first — implementação restante e pré-requisitos operacionais (2026-10-27)

**Correção de contrato API:** PR #1640 corrigiu o parser da chamada GET v2 para o envelope oficial `data.pipelineExecutionSummary`, verificando `planExecutionId`, `orgIdentifier`, `projectIdentifier`, `pipelineIdentifier` e `status`. A versão antiga procurava `data.planExecution.uuid` e falharia com dados válidos. Fonte oficial: https://pkg.go.dev/github.com/harness/mcp-server/common/client/dto e https://apidocs.harness.io/pipeline-execution-details. Rodada após merge: **33 testes Python PASS (0 falhas/erros)** na `main`, executados no Anthares Remote com os módulos carregados em memória, sem credenciais.

**Observador automático implementado e deliberadamente desabilitado:** PR #1646 adicionou `tools/ci_quota_harness_watcher.py` e a etapa **opt-in** ao workflow existente `.github/workflows/ci-quota-external-cancel.yml`. Ele obtém execuções próprias recentes nos commit statuses do GitHub, verifica autor, origem, conta, org, projeto, pipeline e UUID exatos, exige quota **estruturada** em `failureInfo.responseMessages[].code`, cria claim com OIDC e Neon antes de `AbortAll`, verifica terminal e reporta. Não há fallback automático ou bypass de autenticação. O observador é ignorado quando `vars.HARNESS_QUOTA_WATCH_ENABLED != 'true'`. Sem `secrets.HARNESS_API_KEY` ele falha em modo fechado. Prova real de descoberta: GET autenticado como público do endpoint GitHub de statuses retornou 9 registros no commit 66aef1245c04ebd16e0e4e4db593440a2604cc03; 2 execuções próprias distintas passaram a verificação. Nenhum cancelamento real foi iniciado nessa checagem. A etapa principal do Harness CI está preparada para executar a suíte ampliada de 33 testes.

**Correção de expiração do lease:** PR #1648 adicionou `AND lease_until>now()` ao CAS no `provider-cancel.mjs`; antes o report aceitava uma reserva vencida. Contrato Node testado com seis casos, inclusive expiração simulada retornando HTTP 409 `FENCING_REJECTED`. Não pressupor que essa correção está no controlador produtivo até nova implantação.

**Requisitos antes de marcar produção pronta:**
1. Aguardar liberação do bloqueio gratuito Vercel HTTP 402 (`api-deployments-free-per-day`, mais de 100 por dia, `retryAfter=86400` informado em 27/10/2026). Sem comprar plano nem contornar cota. Reconciliar se houve novo deployment concorrente antes de publicar os 8 arquivos completos de `deploy/anthares-ci-quota-controller/` na `main` para o projeto `prj_dIKpIfnkfF2N5eyOdBkrTUfX9ydY`, equipe `team_0LJFNVrGdH5dvDqnTEN3FFoT`. Verificar as rotas existentes e novos claims `provider=harness` com autenticação OIDC legítima.
2. Fornecer uma credencial **autorizada** de Harness para o executor GitHub Actions em `secrets.HARNESS_API_KEY`, nunca em YAML, comentário, log, mensagem ou URL. A ferramenta remota recusou acessar o arquivo DPAPI existente e essa proibição permanece; um navegador logado não prova uma chave API. O usuário não deseja revogar a chave anterior; não fazê-lo automaticamente.
3. Validar GET autenticado do Harness em execução própria (escopo e schema) e cancelamento `AbortAll` **somente** de uma execução própria para homologação com quota comprovada ou execução controlada autorizada, incluindo confirmação de terminal e estado Neon após report. Não cancelar a execução #908 ou outras execuções completadas, nem inventar quota sintética.
4. Somente após essas três comprovações e reconciliação de efeitos, habilitar conscientemente `vars.HARNESS_QUOTA_WATCH_ENABLED='true'` e avaliar separadamente a promoção do roteamento `eligible`/`ci_eligible`. Até lá, ambos permanecem `false`.

Esse estado separa **código implementado e testado**, **descoberta real comprovada**, **ledger Neon real verificado**, **controlador Vercel desatualizado devido à cota**, e **operação real do cancelamento ainda não comprovada**.
