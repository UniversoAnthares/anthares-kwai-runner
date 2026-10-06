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

> Atualizado em 2026-10-05 20:01 -04:00. Os findings append-only continuam sendo a autoridade detalhada.

### Arquitetura comprovada/descartada
- PROVEN: runner público GitHub funciona sem depender da cota do repositório privado.
- PROVEN: vault público validado; PRIVATE_REPO_TOKEN não pertence à arquitetura final.
- PROVEN: Android API 35 x86_64 + tradução ARM; splits Kwai necessários instalam e chegam a KWAI_LAUNCHED.
- ABANDONED: PC como executor/fallback; Oracle; Open Platform Kuaishou como publicador do Kwai brasileiro; Aurora/Play Store como aquisição principal.
- PROVEN EM PRODUÇÃO: Cloudflare control plane v12 foi implantado via Wrangler OAuth a partir de clone fresco. `/health` publica `version=2026-10-05-no-pc-confirmation-v12`, `pc_fallback=false`, estado persistente e fila bound. O PC foi usado somente como console pontual de deploy; runtime continua no Cloudflare.

### Kwai: cadeia causal atual
- PROVEN: FSM state-driven alcança MAIN em múltiplas réplicas e deve ser preservada; não voltar a matrizes pré-normalização.
- UNKNOWN/NOT_TESTED: recovery específico de Pixel Launcher ANR; run 37385649745 teve seis FSM_MAIN_REACHED, mas nenhum job concluído observou LAUNCHER_ANR e quatro foram cancelados.
- PROVEN: Manifest válido no run 37388030409 declarou SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity, LoginActivity, CommonLoginActivity, KwaiAuthActivity e outras.
- IMPORTANTE: SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity e LoginActivity são android:exported=false no Manifest. Permission Denial via adb shell não prova ausência da UI. KwaiAuthActivity/LivePartnerAuthActivity são exported=true.
- PROVEN: run 37388231997 confirmou que cinco Activities internas selecionadas são bloqueadas por `not exported`; isto prova apenas a fronteira de start externo, não ausência da UI. Não repetir `am start` nelas.
- PROVEN: Manifest mostra TinyUserInfoActivity, OpenAuthActivity, KwaiAuthActivity e LivePartnerAuthActivity como entrypoints exportados relevantes; TinyGoogleSSOActivity é exported=false.
- FAILED: run 37389007878 invocou os URI contracts exportados `authorization` com AM_RC=0, mas nenhum expôs UI de login. `ikwai://authorization` caiu em TinyLaunchActivity/diálogo de notificação; as demais rotas caíram no feed/home. Essas quatro rotas permanecem descartadas sem mudança causal.
- PROVEN STATIC CONTRACT: o Manifest válido também mostra `com.kscorp.oversea.platform.router.ui.UriRouterActivity` exported=true com `ikwai://login`/`ikwai://loginchannel` e ACTION_SEND/SEND_MULTIPLE `video/*`. Essas rotas são causalmente distintas das rotas `authorization` já falhas.
- PARTIAL/HARNESS: run 37389749589 preservou o FSM e emitiu `TEST_VALIDITY=FSM_MAIN_REACHED`, alcançou Profile e o estado conhecido `resource downloading`; o workflow expirou enquanto a descoberta interna ainda aguardava o módulo. Ausência de controles de login não foi testada nesse run.
- PROVEN STATIC/SIMULATED: run 37391014212 validou `prepare -> central started -> commit -> verificação específica -> central complete -> CONFIRMED`, com `KWAI_STARTED_BEFORE_COMMIT_STATIC_OK` e `KWAI_PUBLISH_SAFETY_STATIC_OK`. Verificador exige conta esperada + título específico em Profile estável e remove sucesso por marcador genérico de recência.
- RUNNING: run 37391449031 testa, sem publicar, o handoff de uma URI MediaStore exata via ACTION_SEND `video/mp4` para UriRouterActivity. O primeiro run 37391243048 foi INVALID antes da hipótese por `pipefail` sob `/usr/bin/sh`; o rerun usa Bash explícito.
- Publicação real continua em quarentena até identidade/autenticação READY do Kwai. O blocker Cloudflare v12 já foi fechado.

### TikTok: cadeia causal atual
- FAILED/HARNESS: probe 37388273031 expirou esperando marcador de revisão stale; não testou sessão e publish ficou skipped. Probe válido posterior 37389276949 alcançou Render correto e mostrou restore central HTTP 403, bootstrapped=false, identity_verified=false. Fallback por seed de ambiente também FAILED no run 37389620043: revisão correta ativa, mas bootstrapped=false e restore central ainda HTTP 403. Não repetir central GET/env-seed sem mudança causal.
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
- PROVEN EM PRODUÇÃO: `/health` retorna `persistent_state=true`, `queue_bound=true`, `pc_fallback=false`; deploy Cloudflare Version ID `960c9ae5-e3fc-4e9f-b662-7a28dc8b6c6b`.
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
