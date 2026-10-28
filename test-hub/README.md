# Anthares Test Hub

Fonte compartilhada de verdade para testes, decisões e falhas do projeto Anthares remoto.

## Regra obrigatória para qualquer chat/agente

1. Antes de propor, alterar ou repetir um teste, leia este arquivo e os registros relevantes em `test-hub/findings/`.
2. Não repita uma estratégia marcada `FAILED` sem uma mudança explícita que ataque a causa registrada.
3. Não substitua uma estratégia `PROVEN` por hipótese não testada.
4. Ao terminar um teste, crie um NOVO arquivo em `test-hub/findings/`; não edite registros históricos.
5. Se um resultado antigo deixar de valer, crie outro registro com `SUPERSEDES:` apontando para o anterior.
6. Nunca grave secrets, cookies, tokens, senhas ou dados de sessão aqui.
7. Evidência vale mais que descrição: registrar run/job/commit e a linha decisiva do log.

## Estados

- PROVEN: comprovado em teste real.
- FAILED: executado e falhou; não repetir sem alteração causal.
- PARTIAL: parte comprovada, conclusão ainda não.
- RUNNING: teste disparado, sem resultado final.
- SUPERSEDED: registro substituído por evidência posterior.
- ABANDONED: caminho descartado por decisão arquitetural.

## Formato de cada finding

```
# título
STATUS: PROVEN|FAILED|PARTIAL|RUNNING|SUPERSEDED|ABANDONED
AREA: android|kwai|tiktok|cloudflare|github|live|session|architecture
DATE: YYYY-MM-DD
RUN: URL ou none
JOB: URL/id ou none
COMMIT: sha ou none
SUPERSEDES: arquivo ou none

## Objetivo
...

## Resultado
...

## Evidência decisiva
...

## Consequência
O que os próximos chats DEVEM ou NÃO DEVEM fazer.
```

## Estado consolidado atual

> Atualizado em 2026-10-05 20:35 -04:00. Os findings append-only continuam sendo a autoridade detalhada.

### Arquitetura comprovada/descartada
- PROVEN: runner público GitHub funciona sem depender da cota do repositório privado.
- PROVEN: vault público validado; PRIVATE_REPO_TOKEN não pertence à arquitetura final.
- PROVEN: Android API 35 x86_64 + tradução ARM; splits Kwai necessários instalam e chegam a KWAI_LAUNCHED.
- ABANDONED: PC como executor/fallback; Oracle; Open Platform Kuaishou como publicador do Kwai brasileiro; Aurora/Play Store como aquisição principal.
- PROVEN EM PRODUÇÃO: Cloudflare control plane v12 foi implantado via Wrangler OAuth a partir de clone fresco. `/health` publica `version=2026-10-05-no-pc-confirmation-v12`, `pc_fallback=false`, estado persistente e fila bound. O PC foi usado somente como console pontual de deploy; runtime continua no Cloudflare.

### Kwai: cadeia causal atual
- PROVEN: FSM state-driven alcança MAIN em múltiplas réplicas e deve ser preservada; não voltar a matrizes pré-normalização.
- FAILED/OPEN: recovery específico de Pixel Launcher ANR tornou-se gargalo real no run 37392541208: STATE=LAUNCHER_ANR repetiu até FSM_TIMEOUT antes do ACTION_SEND. Esse run não testou SEND. Corrigir recovery causalmente antes de interpretar novos failures pré-MAIN.
- PROVEN: Manifest válido no run 37388030409 declarou SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity, LoginActivity, CommonLoginActivity, KwaiAuthActivity e outras.
- IMPORTANTE: SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity e LoginActivity são android:exported=false no Manifest. Permission Denial via adb shell não prova ausência da UI. KwaiAuthActivity/LivePartnerAuthActivity são exported=true.
- PROVEN: run 37388231997 confirmou que cinco Activities internas selecionadas são bloqueadas por `not exported`; isto prova apenas a fronteira de start externo, não ausência da UI. Não repetir `am start` nelas.
- PROVEN: Manifest mostra TinyUserInfoActivity, OpenAuthActivity, KwaiAuthActivity e LivePartnerAuthActivity como entrypoints exportados relevantes; TinyGoogleSSOActivity é exported=false.
- FAILED: run 37389007878 invocou os URI contracts exportados `authorization` com AM_RC=0, mas nenhum expôs UI de login. `ikwai://authorization` caiu em TinyLaunchActivity/diálogo de notificação; as demais rotas caíram no feed/home. Essas quatro rotas permanecem descartadas sem mudança causal.
- PROVEN STATIC CONTRACT: o Manifest válido também mostra `com.kscorp.oversea.platform.router.ui.UriRouterActivity` exported=true com `ikwai://login`/`ikwai://loginchannel` e ACTION_SEND/SEND_MULTIPLE `video/*`. Essas rotas são causalmente distintas das rotas `authorization` já falhas.
- PARTIAL/HARNESS: run 37389749589 preservou o FSM e emitiu `TEST_VALIDITY=FSM_MAIN_REACHED`, alcançou Profile e o estado conhecido `resource downloading`; o workflow expirou enquanto a descoberta interna ainda aguardava o módulo. Ausência de controles de login não foi testada nesse run.
- PROVEN STATIC/SIMULATED: run 37391014212 validou `prepare -> central started -> commit -> verificação específica -> central complete -> CONFIRMED`, com `KWAI_STARTED_BEFORE_COMMIT_STATIC_OK` e `KWAI_PUBLISH_SAFETY_STATIC_OK`. Verificador exige conta esperada + título específico em Profile estável e remove sucesso por marcador genérico de recência.
- FAILED: run 37395018657 foi válido após FSM_MAIN_REACHED; `ikwai://login` chegou ao UriRouterActivity mas terminou em TinyLaunchActivity/feed, EDITTEXT_COUNT=0, AUTH_HITS vazio. Não repetir bare login-router sem mudança causal. Profile ainda apresenta `resource downloading`; próximo caminho deve ser navegação interna/Agent/Accessibility após módulo disponível.
- Publicação real continua em quarentena até identidade/autenticação READY do Kwai. O blocker Cloudflare v12 já foi fechado.

### TikTok: cadeia causal atual
- PROVEN: run 37395199814 reidratou 21 cookies no Render, confirmou bootstrapped=true e `identity_verified=true`, e persistiu a sessão atualizada no Cloudflare. Não repetir login/rehydrate. O blocker observado no fim do job é somente configuração de mídia: `ANTHARES_VIDEO_SECRET=false` enquanto endpoint/username/user_id estão configurados. Run 37395914027 testa readiness/source discovery sem publicar.
- Modo DIAGNOSTIC atual: 3 posts/dia com observação 3–6h para investigar baixa distribuição. A meta/capacidade de produção 100/dia permanece separada; nenhum modo deve ser usado como prova do outro.
- O caminho workflow_dispatch de tiktok-real-publish ainda não satisfaz aceitação production-PROVEN: precisa alinhar endpoint ativo, validar identidade imediatamente antes, verificar o novo post independentemente e fechar ledger/estado incerto.

### Control plane / fila
- PROVEN EM PRODUÇÃO v12: PC/local, Google e Oracle foram removidos do roteamento. `/strategy` publica cuts Render→GitHub; TikTok Render→GitHub; Kwai GitHub; Kwai LIVE HLS origin→GitHub; control Cloudflare→GitHub→Render.
- PROVEN EM PRODUÇÃO v12: `/failover-self-test` retorna Render→GitHub→null, `local_retired=true`; não existe executor local após falha do GitHub.
- PROVEN: complete()/reconcile() são fail-closed no v12 implantado: confirmação positiva exige estado anterior válido, publication_started quando aplicável e remote_id/confirmation_evidence; a prova estática correspondente é o run 37388863529.
- O hub tinha RUNNING obsoletos; findings QA recentes os supersedem. Sempre verificar o finding mais novo antes de usar o resumo.

### Control plane central
- PROVEN EM PRODUÇÃO: Durable Object SQLite cobre enqueue/lease/started/complete/fail/reconcile, dedupe por chave e overlap temporal, UNCERTAIN e circuit breaker no Worker v12 implantado.
- PROVEN EM PRODUÇÃO: allowlist OIDC, confirmação fail-closed, PC/Google/Oracle removidos e HLS sem fallback WordPress hardcoded estão ativos na versão `2026-10-05-no-pc-confirmation-v12`.
- PROVEN EM PRODUÇÃO v16: `/health` retorna `version=2026-10-05-queue-fencing-v16`, `persistent_state=true`, `queue_bound=true`, `pc_fallback=false`; Cloudflare Version ID `1a25c85d-aea3-4bc9-8a8b-5fcedef7abcd`. Run 37396894429 / job 112054896540.
- PROVEN EM PRODUÇÃO v16: cada aquisição incrementa `lease_generation`; holders obsoletos são rejeitados em `started`, `complete` e `fail`; crash antes de `publication_started` é recuperável e crash/expiração depois de `publication_started` permanece `UNCERTAIN` até reconciliação.
- HANDOFF kwai-publish: o cliente `kwai_queue_state.sh` ainda está pinado em v15 e não envia `lease_generation` nem operação `renew`. Deve ser migrado pelo agente que detém o lease `kwai-publish`; o v16 falha fechado até essa migração.
- PROVEN EM PRODUÇÃO v15: `/health` retorna `version=2026-10-05-queue-heartbeat-renew-v15`, `persistent_state=true`, `queue_bound=true`, `pc_fallback=false`; run 37395158585.
- PROVEN EM PRODUÇÃO v15: além de owner/estado/expiração e single-job double-claim, o self-test comprova `lease_renew_repeated=true`, isto é, renovação repetida/heartbeat durante execução longa. Run 37395158585 / job 112049276852.
- PROVEN EM PRODUÇÃO v14: sucesso confirmado limpa o circuit breaker (`disabled_until=null`) junto com os contadores de falha; regressão detectada no run v13 37394632606 e fechada no v14.
- O caminho automático conhecido via runner público continua sem `CLOUDFLARE_API_TOKEN`; isso deixou de bloquear a versão atual porque o deploy v12 foi concluído pela sessão Wrangler OAuth autorizada. Não reabrir o caminho de deploy antigo sem mudança causal.

### Regra experimental obrigatória
Antes de disparar novo teste, o finding RUNNING deve declarar:
1. BASELINE_PROVEN: finding/estado comprovado do qual parte.
2. FAILED_AVOIDED: FAILED relevantes e a alteração causal que impede repetição.
3. SUCCESS_SIGNAL: evidência observável necessária para considerar sucesso.
4. FAILURE_SIGNAL: evidência observável que encerra/refuta a hipótese.
5. TEST_VALIDITY: como detectar falha do próprio harness; falha do harness não conta contra a hipótese.

Não abrir nova matriz enquanto existir run causal relevante RUNNING, salvo camada independente. Job verde sem SUCCESS_SIGNAL explícito não é PROVEN.

## Concorrência
O diretório `findings/` é append-only. Antes de novo experimento, consultar findings recentes e runs em andamento. Se dois chats atuam na mesma cadeia causal, o run mais recente declarado RUNNING tem precedência até produzir evidência.


## Lease obrigatório para mutações

Diagnósticos somente-leitura podem ser paralelos. Toda mutação de código/deploy/sessão/fila/publicação precisa de lease append-only antes da ação.

O agente deve:
- atualizar README + todos os findings/commits novos desde seu último snapshot;
- conferir runs/deploys RUNNING da mesma cadeia causal;
- criar finding `lease-<area>-<objetivo>` com baseline, FAILED evitados, sinais de sucesso/falha/validade e expiração máxima de 30 min;
- reler HEAD após criar o lease e ceder se já existir lease ativo anterior da mesma área;
- invalidar, em vez de classificar FAILED, qualquer teste cujo baseline/deploy mudou durante a execução;
- encerrar o lease com novo finding append-only baseado em evidência.

Áreas de mutação são serializadas: `tiktok-session`, `tiktok-publish`, `kwai-login`, `kwai-publish`, `kwai-live`, `cloudflare-control`, `queue`.

A existência de um lease ativo não impede probes somente-leitura, mas impede outro deploy/mudança de estado na mesma área.


### QA closure — TikTok canary media / WordPress inventory (2026-10-06 02:51Z)
- PROVEN: cloud synthetic canary MP4 preparation. Run 37405248345 emitted CANARY_MEDIA_HARNESS=PROVEN for imageio_ffmpeg, apt_ffmpeg and docker_ffmpeg. Preserve imageio_ffmpeg as canonical no-PC preparation path.
- INVALID (do not count as FAILED): run 37405252389 WordPress filename reconstruction 5-way; all five jobs emitted TEST_VALIDITY=INVALID because the newest REST video record lacked media_details.file.
- PARTIAL/PROVEN INVENTORY BASELINE: successor run 37405510219 validly inspected 191 REST video records; all are video/mp4, all expose source_url/slug/top-level filename, only 73 expose media_details/filesize. Physical MP4 byte retrieval remains unproven.
- Canonical findings: test-hub/findings/20261006-0249-qa-tiktok-canary-media-harness-proven.md and test-hub/findings/20261006-0251-qa-tiktok-wp-inventory-canonical-closure.md.
- Consequence: the TikTok real canary no longer depends on WordPress media recovery; its ffmpeg/media-preparation blocker is closed. WordPress retrieval can continue independently from the 191-record inventory if needed.


## QA closure 2026-10-06 — items 2-4
- **Kwai publish safety: PROVEN.** Final CHAT2 acceptance run 37410436742 passed all 24 implementation/safety checks. Real Kwai publication remains gated by authenticated `kwai-login READY` and therefore is not claimed as proven.
- **TikTok media/publisher: PROVEN.** Controlled MP4 generation and the Render publisher path are proven. The current real-canary blocker is session restoration: current diagnostics show `bootstrapped=false`, `identity_verified=false`, `ready_for_tiktok=false`, with central restore HTTP 403 and direct central-session HTTP 401. A prior allowlisted observation run 37409026789 successfully read 21 central cookies; the current OIDC/control authorization has regressed or changed outside this repository.
- **Adversarial control contracts: PROVEN.** UNCERTAIN, observation-only reconcile, evidence-gated complete, lease_generation fencing, heartbeat, no-PC path and serialized real-publish gate passed the final CHAT2 acceptance.
- **Final project acceptance remains OPEN** until `TIKTOK_REAL_REMOTE_POST=PROVEN` and `KWAI_REAL_REMOTE_POST=PROVEN` both have independent verification and ledger confirmation.
- Canonical QA finding: `test-hub/findings/20261006-qa-items-2-4-final-state.md`.


## QA execution round — four immediate fronts
- TikTok OIDC: repository contains the allowlist fix for `tiktok-reconcile-v2.yml`, but current deployed control plane still returns HTTP 401 on run 37411367637. Do not repeat until the SHA is deployed.
- Render TikTok publisher: latest deployment `c57af706086399b058690510cb20c289fa7ab468` is LIVE; Render is not the current blocker.
- Kwai login: active `kwai-login` lease remains authoritative; no competing mutation performed.
- Final SHA dedupe QA: run 37411496459 passed all 5 current cases with explicit PROVEN signals.
- Whole-project audit: no unowned immediate implementation gap found. Final acceptance still requires independent real-post proof for TikTok and Kwai.
- Canonical finding: `test-hub/findings/20261006-qa-four-fronts-execution-round.md`.


## OIDC closure — 2026-10-06 05:31Z
- PROVEN: the reviewed GitHub OIDC allowlist source was deployed to the Cloudflare control plane through Wrangler OAuth from a fresh clone.
- PROVEN: protected TikTok Central Session Read Probe run 37418647980 completed SUCCESS post-deploy; the deployed-control HTTP 401 blocker is closed.
- Preserve current queue-fencing v16 semantics. Continue TikTok only under the serialized tiktok-publish lease.
- Canonical finding: test-hub/findings/20261006-0531-cloudflare-tiktok-oidc-deploy-proven.md.


### Arquitetura dual-provider — 2026-10-07
- PROVEN: `tools/provider_router.py` implementa GitHub/GitLab como peers, seleção alternada, single-writer lease, lease generation, checkpoint fencing e failover condicionado a provider indisponível + HEAD idêntico.
- PROVEN: workflow público `37675173709` / job `112976698070` executou os 6 testes do roteador e terminou `success`.
- A persistência de lease/checkpoint permanece no `anthares-control`; o módulo do runner é a política determinística e não cria um segundo controller.


### Claude MCP authorization — 2026-10-19 11:05 UTC
- PARTIAL: missing Cloudflare sender-domain configuration was isolated; official GitHub owner identity fallback is deployed, with PKCE, encrypted browser state, identity allowlist and single-use codes preserved.
- PROVEN: real Claude Free login and consent page request ara.read/github.read/github.write; 19 Node tests, signed capabilities regression and live discovery/negative checks pass. Existing ChatGPT Remote remains operational.
- Latest Worker: 13f5ee1d-33fd-4310-b2ca-f16e1b2871ca, PR162 source5306fbf2. Scoped GitHub edits now use atomic expectedHeadOid; begin_task returns the post-lease base SHA.
- PENDING: actual GitHub visible owner consent, provider callback, Claude-issued file read/edit and draft PR. GitHub requires a visible focused authorization page; Anthares Remote explicitly forbids interactive focus manipulation. Owner action is pending; no complete integration claim is authorized.
- Canonical evidence: test-hub/findings/20261019-1105-claude-oauth-interoperability-and-branch-fencing-partial.md. Recovery lease closed pending the interactive gate; fresh lease required before further mutation.


### Claude MCP real acceptance — 2026-10-19 12:16 UTC
- PROVEN: owner's Claude Free session has Anthares connected and 20 tools. Real Claude calls read GitHub AGENTS.md/README and consulted connected Anthares Remote.
- PROVEN: Claude acquired a lease, created claude/mcp-acceptance-20261019-1210, wrote and reread one disposable file, and opened draft PR #164. Independent GitHub verification confirms commit 2c320a373c648b13f9766d192cc15c0d181ceeb8 and blob 8afd94029eb32b7661540a03a3a17f9908375785. Do not merge the disposable test PR.
- Latest Worker: 24ffad76-20a0-4911-b6c9-465ad1b135b2, source dd14ef5d in integration PR162; 23 Node/workerd tests plus signed capabilities regression pass. GitHub identity OAuth is operational; email sender-domain delivery remains unavailable.
- Scope boundary: Claude Remote remains read-only; arbitrary command/test execution is not exposed. PR162 is deployed but remains draft/unmerged. No whole-project publication acceptance is implied.
- Canonical evidence: test-hub/findings/20261019-1216-claude-mcp-real-acceptance-proven.md, superseding the earlier partial authorization state and closing both recovery and acceptance leases.


### Claude operational closure — 2026-10-19 18:48 UTC
- DONE: PR162 merged as 4385a0f49f4ce3bcc9bd05f1dd1689e61d3324e9; operational docs PR191 merged as 001c47e4aa067b90f58ea747baac3fa3ab37c87a. Owner GitHub identity OAuth is canonical; email is not an integration dependency.
- DONE: fixed run_tests suite implemented and deployed in Worker f69e09b4-4ef2-48f5-acaf-fed056d462e2, exact reviewed source pin 30217080974912cbfc049072b844f473a69c0e27. Actual Anthares Remote runner returned 26 pass, 0 fail and capabilities_passed=true under the renewed current-time lease. Arbitrary shell and unreviewed branch-code execution remain denied.
- PROVEN: live control/device health and anonymous MCP 401. Previous actual Claude owner OAuth, read/write and draft PR164 acceptance remain valid. Do not merge disposable PR164.
- BLOCKED EXTERNALLY: Claude Free exhausted its five-hour message quota and refused the new run_tests prompt before issuing any tool call; UI reports reset at 18:00. Only acceptance of the new test tool through Claude remains unproved. No paid upgrade, identity switching or repeated quota retries.
- Evidence and lease closure: test-hub/findings/20261019-1848-claude-final-merge-and-approved-tests.md. Future acceptance needs a fresh lease. No CORTES/Android/SSH behavior changed.

## Claude Code remoto gratuito — 2026-10-19
- PROVEN: GitHub Actions efêmero, sem VPS e sem dependência de PC, inicializa Claude Code e 9Router em loopback com Gemini recuperado do Bitwarden. Planejamento: run 39336129062, ANTHARES_CLAUDE_REAL_CANARY=PASS.
- PROVEN: fallback de modelo propositalmente indisponível para outro modelo com resposta real; edição de arquivo real isolada, validada como única alteração. Run 39337326780: ANTHARES_FREE_FAILOVER_REAL=PASS, ANTHARES_FREE_CLAUDE_REAL_EDIT=PASS. Documento de prova no PR rascunho #209; não fazer merge automático.
- PROVEN em modo degradado: com dois modelos externos indisponíveis por 429/rede, o modelo Gemini 3.5 Flash-Lite concluiu a operação; novos runs reavaliam três modelos.
- PROVEN: autorização de PR automático corrigida. Após o usuário salvar a permissão, o GitHub Actions criou sozinho o PR rascunho #212, autor github-actions[bot], no run 39339550110; log ANTHARES_FREE_AUTO_PR=PASS. Não fazer merge do PR de prova.
- Fontes: test-hub/findings/20261019-2250-free-claude-code-remote-real-proven.md e test-hub/findings/20261019-2308-free-claude-autopr-proven.md. Sem mudanças no Anthares AI Hub, WordPress, CORTES ou contas pagas.

## Delegação direta Claude Free → GitHub Claude Code — 2026-10-20
- PROVEN: PR #214 integrado, deploy Cloudflare run 39345333579 completou; Worker versão dc6408ba-02fa-4ab5-a439-1760d3ec571e. OAuth proprietário, Anthares Remote ativo e bloqueio anônimo HTTP 401 preservados.
- PROVEN: testes da ponte, compilação Wrangler e escopos MCP run 39345229461. Ferramentas novas: run_claude_code (github.write), get_claude_code_status e get_claude_code_result (github.read). Nenhum servidor pago nem PC usados como executor.
- PENDING OWNER ACCEPTANCE: a sessão Claude do proprietário deve enviar uma tarefa real e consultar seu status e resultado. A permissão Actions:write do token GitHub guardado em Cloudflare ainda precisa ser comprovada nessa chamada real; não afirmar end-to-end.
- Fonte: test-hub/findings/20261020-0005-claude-mcp-delegation-deployed-partial.md. Lease de desenvolvimento encerrado; preservar OAuth e os trabalhos Anthares existentes.


## Anthares ChatGPT + Claude Code + Work — 2026-10-20

- **PROVEN (code tests only):** PR #226 builds an owner-only, plan-only GitHub Issues collaboration gateway, deterministic idempotent dispatch, main-branch bot authority bound to exact owner issue/task/UUID, Claude Free read-only `collab_list_tasks` / `collab_get_task`, and Work via GitHub connector. CI runs 39355622185 (39 tests PASS), 39355622093 (Cloudflare build PASS) and 39355622176 (Claude runner static-check PASS).
- **PARTIAL (deployment):** PR #226 must merge onto protected main before the issue-created workflow or new Claude MCP tools can be accepted as production-live. Issue #222 is design/owner identity evidence only; not a dispatched task. The existing independent Claude Free -> Claude Code remote run 39352658418 remains PROVEN.
- **BLOCKER:** existing ruleset `proteger-main` rejected PR #218 merge; never bypass. Work execution can only be attested inside actual Work mode with authorized GitHub connection, not in this Chat session.
- Full finding: `test-hub/findings/20261020-0152-multiagent-work-collab-partial.md`. Do not claim real multiagent orchestration PROVEN before owner-authored issue canary, actual remote result, Claude MCP tool read and Work session review.

- **PROVEN production upgrade (2026-10-20):** Live ChatGPT issue #230 -> gateway GitHub Actions run 39356597262 -> owner-issue-fenced bot -> Claude Code run 39356635285 (`completed/success`) -> ZIP STORE artifact 12235437781 begins with `ANTHARES_COLLAB_CHATGPT_WORK_OK`; gateway final issue comment `COMPLETED conclusion=success`. Worker deployment 39355914581 succeeded with owner OAuth and anonymous MCP 401. Prior issue #227 timed out inside 9Router; remained no-redelivery and was fixed by bounded harmless probe retry PR #229. **Claude MCP owner UI read-tool refresh and Work-mode session consumption are separately NOT_TESTED**. Evidence: `test-hub/findings/20261020-0211-chatgpt-claude-multiagent-real-proven.md`.


## MCP Cloudflare 1.1.0 + Work handoff (2026-10-20)
- **PROVEN deployment:** PR #218 (catálogo MCP) and PR #233 (propagation gate, OTP legacy auto-deploy disabled) merged through reviewed PR. Canonical Cloudflare run 39358082325 completed SUCCESS, emitted ANTHARES_CLAUDE_NEW_TOOLS_LIVE=PASS and ANTHARES_CLAUDE_BRIDGE_ANON_MCP_DENIED=PASS; independent health GitHub owner OAuth, control_ready, MCP version 1.1.0, 3 Claude Code tools. Previously run 39357593535 deployed but failed verification due immediate version check; corrected. OTP legacy run 39357593404 failed safe preflight; no OTP auto-run on PR #233 merge.
- **PROVEN ChatGPT→Claude Code:** shared Issue #230, remote run 39356635285 and accepted artifact. **WORK READY, NOT EXECUTED:** owner handoff issue #234 is prepared, but a real Work session must be initiated and submit its own review. Extra read-only `collab_get_task` in Claude's owner UI still needs an actual Claude call to prove client refresh. Evidence: `test-hub/findings/20261020-0224-mcp-1-1-and-work-ready-proven.md`.

### Threads — fechamento editorial em lote (2026-10-27)
- **PROVEN:** o run [40565169978](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40565169978) gerou 149 transcrições e hashes de mídia verificados; cinco casos ruidosos foram reavaliados pelo run [40568800225](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40568800225).
- **PROVEN EM NEON:** 149 quarentenas editoriais resolvidas após integração de prova e metadados no GitHub; resultado final: 131 confirmadas, 162 queued elegíveis, **zero isolated**; primário cloud desativado e nenhuma execução em curso.
- Registro detalhado: `test-hub/findings/2026-10-27-threads-asr-149-proven.md`. Isso não autoriza publicação nem ativação do cloud primary sem fencing.

### AOI item fixo 9 — supervisão e alertas P0 externos PROVEN (2026-10-28)
- GitHub Issues é a autoridade dos incidentes P0; a detecção externa roda em **GitHub-hosted Ubuntu 24.04**, sem depender do runner Windows ou Codeberg. Forgejo CI sandbox mantém QA não publicador a cada 12 horas.
- **PROVEN:** [job 123145935173](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40782057532/job/123145935173) concluiu SUCCESS e registrou `QA_P0_CLOUD_ALERT_DELIVERED=PASS` na issue real #1780, comentário 6482589037; readback GET confirmou entrega, 0 tickets duplicados e 2 fingerprints reconciliados.
- A rota hospedada tem concorrência própria e continua operacional mesmo com a job Windows queued. Leitura autenticada WordPress pelo Windows é preservada; **reparação de incidentes é item 16**.
- Finding append-only: `test-hub/findings/20261028-qa-p0-hosted-alert-delivery-proven.md`, que supera o finding RUNNING do mesmo escopo.

### AOI item fixo 17 — Codeberg aposentado como primário (2026-10-28)
- GitHub canônico; GitLab e Forgejo Hostinger são redundâncias condicionadas a paridade recente. Codeberg suspenso permanece excluído de execução, CI, Git, QA e publicação.
- **Quarentena comprovada em fonte:** 27/27 workflows históricos `.forgejo/workflows/` sem gatilhos automáticos; 28/28 jobs com `if: false`. Os 13 workflows Codeberg-only do GitHub também estão inertes; as rotas independentes Git/QA possuem recibos reais anteriores.
- A promoção de produtores/publicadores continua separadamente controlada pelos itens 1, 2, 3 e 15; o CI principal Forgejo está em revisão separada. O item 13 mantém os históricos GitLab sob revisão.
- Registro de evidência: `test-hub/findings/20261028-item17-codeberg-retired-proven.md`.
