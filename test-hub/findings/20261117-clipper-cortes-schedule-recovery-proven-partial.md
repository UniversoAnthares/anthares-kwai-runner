# Clipper/CORTES — recuperação de agendamento e modo seguro de falha WordPress
STATUS: PARTIAL
AREA: github
DATE: 2026-11-17
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/44128263410
JOB: 134197934871 / Clipper Cloud
COMMIT: 0ef97a33f622fd0dc33825b98bb32ba038ab3579
SUPERSEDES: none
VERIFIED_UTC: 2026-11-17T16:41:00Z
OWNER: ChatGPT / recuperação Clipper e CORTES

## Objetivo
Restaurar disparos operacionais Clipper e CORTES após cron ausente, preservar dedupe/fonte e prover monitoramento fora do próprio agendador GitHub, sem interação gráfica do Windows.

## Evidências decisivas
1. Clipper `clipper.yml` era `disabled_manually` desde 31/10; só executara falhas em 30/10. O novo workflow mantém UM job hospedado, sem renderização automática de lives na máquina pessoal. PR #317 incorporada no commit `be8b3d6a05b941a78b8c5dedd870016e7ef0aeb8`.
2. CORTES diário ativo com cron 10:40Z: 16/11 `schedule` iniciou às 20:39Z, cerca de 10h atrasado; 17/11 sem execução até a intervenção. A execução source-only #44125092451 concluiu com success, confirmou `CORTES_SOURCE_LOCK_HELD source=cOhqEaY3-08` e `CORTES_PREVIOUS_DAY_GENERATION_RESUME`. Jobs long/batch/dispatch foram skipped de modo seguro.
3. Ampliadas janelas de `cortes-6am-rescue.yml`; corrigidas expectativas dos testes para 06h40 local; CI hosted #44126580662 e PR #317 tiveram sucesso.
4. Clipper recuperado com `workflow enable`; a primeira tentativa #44126804566 falhou na consulta `POST /wp-json/anthares/v1/video-storage` com HTTP 504, sem upload efetuado. PR #318 incorporada commit `fa886eac827a1a30dff25f55fd32d706c864af3d` adicionou modo fail-closed: somente cloud e status HTTP 502/503/504 podem passar a reconciliação de mídias já armazenadas, com novos uploads bloqueados se status incerto. Testes hospedados #44128145456 success. Retry causal #44128263410 completed success, WordPress autenticado, agenda YouTube reconciliada e fila manual vazia.
5. Nove segmentos de 229 da fonte `cOhqEaY3-08:g1` tinham `editorial_pending_retry` por `CORTES_STRATEGIC_EDITORIAL_REQUIRED`, sem attachment; 218 stored e 2 descartados por duração. O primeiro AI devolvia `needs_review` e era isolado antes do reparo. PR #319 incorporada commit `0ef97a33f622fd0dc33825b98bb32ba038ab3579` habilita reparo estrito limitado com prova literal, testes hosted #44128495130 success. A produção dos nove ainda precisa de executor de mídia externo com ledger e guard de admissão homologados; nenhum upload foi feito nessa correção.
6. Criado monitor recorrente de agendamentos em ChatGPT, independente dos eventos `on.schedule` do GitHub, com verificação diária de hora em hora entre 07h10 e 22h10 America/Campo_Grande a partir de 18/11; despachos condicionados à ausência de execução concorrente, quotas, autenticação e idempotência. Existe dependência comum do GitHub para o executor, portanto o monitor não equivale a contingência computacional independente.

## Estado e pendências
PROVEN: execução hospedada Clipper voltou e terminou com sucesso; descoberta CORTES source-only voltou, fonte preservada; regressões de código aprovadas e incorporadas.
PARTIAL: producer CORTES de mídia ainda depende do workflow self-hosted Windows; nove segmentos editoriais aguardam processamento autorizado, e 36 entradas Kwai seguem em quarentena sem reenvio. Nenhum registro de publicação incerta foi promovido.
OPEN: implantação de executor cloud independente para renderização com storage/ledger remotos, reconciliação Kwai, falha de sessão Instagram e Shorts YouTube.
SEGURANÇA: nenhuma janela PowerShell, mouse, teclado, áudio ou execução de renderização no PC do titular; automação de acompanhamento deve observar essa restrição.

## Consequência
Não confundir workflow source-only verde com geração final de curtos. Nunca reativar produtor Windows para comprovar cron. Produção só depois de lease, prova da mesma fonte, quotas e armazenamento externo homologado; continuar CI em GitHub hospedado. Evitar múltiplos executores/publicações; conferir IDs remotos para cada confirmação.
