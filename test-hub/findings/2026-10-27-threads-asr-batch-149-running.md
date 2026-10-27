# Threads — lote externo com 149 comprovações
STATUS: RUNNING
AREA: github
DATE: 2026-10-27
RUN: pending PR
JOB: 15 jobs max-parallel 5
COMMIT: db21d102b9b40569759e07f70a6573fb4f4190e8
SUPERSEDES: none

## BASELINE_PROVEN
149 cortes queued/isolated editorial missing no Neon; hash de mídia pinado individualmente no manifesto. ASR externo por GitHub Actions comprovado nos runs 40555639112, 40557176337, 40559374218, 40559887663.

## FAILED_AVOIDED
Não usar PC como destino/staging. Não publicar, não liberar status automaticamente, não usar cookies/secrets, não repetir fluxo pontual centenas de vezes.

## SUCCESS_SIGNAL
Para cada corte: ASR_VERIFIED com WP attachment real, hash igual ao manifesto e transcrição/artefato comprovado. Job sem evidencia não conta.

## FAILURE_SIGNAL
Cota, timeout, mídia inexistente/sha diferente, texto curto, job failed; manter isolated. Cota confirmada => cancelar job ainda executando antes de transferir; não usar redundância sem lease.

## TEST_VALIDITY
Somente evidências individuais conferidas contra Neon autorizam promoção na registry. Status verde do job não prova todos os itens; resumo e outputs por clipe exigidos.
