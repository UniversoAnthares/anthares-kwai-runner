# Lease — fila social: ACKs fail-closed e resultados ambíguos
STATUS: RUNNING
AREA: architecture
LEASE_AREA: queue
LEASE_OWNER: Manus task fC58le6HtsUjTsBorwFbaA
LEASE_EXPIRES: 2026-10-07T17:10:00Z
DATE: 2026-10-07
RUN: none
JOB: fC58le6HtsUjTsBorwFbaA
COMMIT: anthares-clipper `26e6fb8bc425ea0bb7610c5fd3d5df0b2b0bf097`; anthares-wordpress `a26053a0303b41114ad0b10d4e6ea493970b70f5`; hub main `a405a57f45ddd7fe0971779590fcf707ce305c30`
SUPERSEDES: none

## Objetivo

Em branches/PRs sem merge, endurecer a fila de publicação social para que claim/start/result só prossigam com ACK explícito, resultados de POST final ambíguos nunca virem retry automático, e uma entrega cujo `publication_started_at` esteja definido não seja re-claimada automaticamente após expiração do lock. Preservar o cron social existente; não publicar nem executar o workflow.

## Baseline comprovado

- `anthares-clipper/social_api_publisher.py` ignora `ok` em claim/started/result e converte qualquer exceção em `retry`, mesmo depois de um POST público poder ter sido aceito.
- `anthares-wordpress/anthares-tiktok-distributor/includes/class-atd-db.php` permite re-claim de linhas `claimed` expiradas sem condicionar a `publication_started_at IS NULL`; o claim reseta `publication_started_at`.
- `ATD_API::publisher_started` e `publisher_result` retornam `{ok:true}` quando a operação é aceita; falhas do banco são `WP_Error`/HTTP não-2xx. `finish_delivery` aceita `needs_human` e exige `remote_id` + `confirmation_evidence` para `published`.
- Nenhum lease com expiração futura foi encontrado no hub na consulta das 16:43Z. Run em andamento `Kwai Emulator Boot Diagnostic #37652802571` pertence a `main` do runner e não é o publisher social; não será tocado.

## FAILED_AVOIDED

Não repetir retries automáticos após tentativa de publicação externa ambígua; não tratar JSON HTTP 200 com `ok:false` como claim/start/result aceito; não reabrir automaticamente uma entrega já marcada como iniciada. Não executar `workflow_dispatch`, cron, API externa, upload ou publicação; não desabilitar schedule.

## SUCCESS_SIGNAL

Testes offline/mocked comprovam: `ok:false` bloqueia qualquer chamada ao provider; erro antes do POST final resulta em retry controlado; erro/timeout depois de iniciar o POST final resulta em `needs_human`, nunca `retry`; ACK `published` só considera sucesso `ok:true`; logs não revelam access tokens em query; claim expirado somente é reaberto quando ainda não houve `publication_started_at`.

## FAILURE_SIGNAL

Qualquer teste mostra chamada pública após claim/start não reconhecido, retry automático depois de POST final iniciado, token/URL sensível em mensagem de erro ou reclaim de linha já iniciada.

## TEST_VALIDITY

Somente mocks para API/funções do provider e testes estáticos/unitários locais; nenhum segredo é lido; rede externa desabilitada para os testes; nenhum workflow é disparado. Se qualquer SHA de baseline mudar durante o patch, pausar e reauditar o delta antes de prosseguir.

## Escopo autorizado

Apenas `anthares-clipper` (publisher social e testes; workflow para escopo de secrets somente) e `anthares-wordpress` (claim da tabela de deliveries e teste de regressão). Alterações ficarão em branches/PRs abertos e não serão mescladas por esta tarefa.
