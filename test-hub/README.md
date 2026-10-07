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

### Lease candidato registrado em branch/PR (não mesclado)
- Área serializada: `queue`; escopo: ACKs do publisher social em `anthares-clipper`, reclaim de delivery iniciado e ACK HTTP dos handlers `publisher_started`/`publisher_result` em `anthares-wordpress`.
- Finding: `test-hub/findings/20261007-lease-queue-social-publisher-acks.md`; expira em `2026-10-07T17:10:00Z`.
- Extensão append-only: `test-hub/findings/20261007-lease-queue-social-publisher-acks-addendum.md`.
- Este registro está em branch/PR porque a instrução do usuário proíbe merge nesta tarefa; ele não altera o estado de `main`.

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
