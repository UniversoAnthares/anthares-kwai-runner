# Lease TikTok upload-path recovery
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
EXPIRES: 2026-10-06T16:15:00Z

## Objetivo
Corrigir Direct Post que falha antes da API com file_missing apesar de existirem MP4 no uploads.

## BASELINE_PROVEN
OAuth Sandbox e creator_info Content Posting API confirmados. Direct Post falhou localmente com arquivo ausente.

## FAILED_AVOIDED
Não repetir publicação com o mesmo resolver. Mudança causal: fallback restrito ao uploads, por basename, exigindo arquivo regular legível e correspondência única.

## SUCCESS_SIGNAL
Resolver encontra arquivo real do item e o fluxo avança além de file_missing.

## FAILURE_SIGNAL
Resolver continua retornando file_missing ou encontra correspondência ambígua.

## TEST_VALIDITY
PHP lint + verificação de que o fallback permanece confinado ao basedir de uploads.
