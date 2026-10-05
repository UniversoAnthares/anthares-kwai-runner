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

> Atualizado em 2026-10-05 19:28 -04:00 pelo CHAT 5/QA. Os findings append-only continuam sendo a autoridade detalhada.

### Arquitetura comprovada/descartada
- PROVEN: runner público GitHub funciona sem depender da cota do repositório privado.
- PROVEN: vault público validado; PRIVATE_REPO_TOKEN não pertence à arquitetura final.
- PROVEN: Android API 35 x86_64 + tradução ARM; splits Kwai necessários instalam e chegam a KWAI_LAUNCHED.
- ABANDONED: PC como executor/fallback; Oracle; Open Platform Kuaishou como publicador do Kwai brasileiro; Aurora/Play Store como aquisição principal.
- Cloudflare: snapshot atual contém fila Durable Object, dedupe temporal e correção OIDC, mas o deploy público 37387933513 NÃO chegou ao Wrangler porque CLOUDFLARE_API_TOKEN estava vazio. Código implementado não equivale a deploy production-PROVEN.

### Kwai: cadeia causal atual
- PROVEN: FSM state-driven alcança MAIN em múltiplas réplicas e deve ser preservada; não voltar a matrizes pré-normalização.
- UNKNOWN/NOT_TESTED: recovery específico de Pixel Launcher ANR; run 37385649745 teve seis FSM_MAIN_REACHED, mas nenhum job concluído observou LAUNCHER_ANR e quatro foram cancelados.
- PROVEN: Manifest válido no run 37388030409 declarou SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity, LoginActivity, CommonLoginActivity, KwaiAuthActivity e outras.
- IMPORTANTE: SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity e LoginActivity são android:exported=false no Manifest. Permission Denial via adb shell não prova ausência da UI. KwaiAuthActivity/LivePartnerAuthActivity são exported=true.
- RUNNING: Kwai Declared Login Activity Probe 37388231997. Interpretar separadamente permissão de start e existência de UI; não classificar Activities internas como inexistentes por Permission Denial.
- PROVEN somente STATIC/SIMULATED: Kwai publish safety run 37387709252 emitiu KWAI_PUBLISH_SAFETY_STATIC_OK. Publicação real continua sem prova e o workflow real está fail-closed até READY.

### TikTok: cadeia causal atual
- RUNNING: session restore/identity probe 37388273031; job publish está skipped nesse push e não deve ser confundido com publicação real.
- Modo DIAGNOSTIC atual: 3 posts/dia com observação 3–6h para investigar baixa distribuição. A meta/capacidade de produção 100/dia permanece separada; nenhum modo deve ser usado como prova do outro.
- O caminho workflow_dispatch de tiktok-real-publish ainda não satisfaz aceitação production-PROVEN: precisa alinhar endpoint ativo, validar identidade imediatamente antes, verificar o novo post independentemente e fechar ledger/estado incerto.

### Control plane / fila
- Snapshot atual ainda contém prioridades/fallback `local`; CHAT 4 possui lease ativo para removê-lo e endurecer invariantes.
- QA encontrou que complete()/reconcile() ainda confiam em `confirmed=true` do chamador com validação insuficiente do estado anterior/publication_started/evidência. Não classificar queue safety como fechada até o controlador rejeitar confirmação prematura.
- O hub tinha RUNNING obsoletos; findings QA recentes os supersedem. Sempre verificar o finding mais novo antes de usar o resumo.

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
