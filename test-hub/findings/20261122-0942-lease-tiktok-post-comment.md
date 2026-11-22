# Lease: TikTok per-confirmed-publication comment
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-11-22
RUN: none
JOB: anthares-clipper user request
COMMIT: 0eaf46311f406247cf5967fc1bd123699cffc441
SUPERSEDES: none
LEASE_OWNER: chatgpt-gpt6-cortes-tiktok-engagement-20261122
LEASE_EXPIRES: 2026-11-22T10:12:00-04:00

## Objetivo
Implementar uma tentativa de comentário genérico por publicação TikTok confirmada em @universo.anthares e @lucasrosalem4, seleção aleatória de vídeo, histórico das 30 mensagens, idempotência por conta e publicação e isolamento da rotina de upload.

## BASELINE_PROVEN
Filas Neon separadas e publicadores cloud com STARTED/CONFIRMED; publicação permanece independente da ação auxiliar.

## FAILED_AVOIDED
Estado local efêmero; repetição de comentário após timeout; conta trocada; bypass de captcha/429; mudança no fluxo de upload já confirmado.

## SUCCESS_SIGNAL
PR com os dois pontos pós-confirmação, armazenamento persistente por conta e remote id, testes de isolamento e duplicação.

## FAILURE_SIGNAL
Duas tentativas para mesmo vídeo, comentário antes da confirmação, repetição das 30 mensagens anteriores ou exceção que interrompa a publicação.

## TEST_VALIDITY
Testes determinísticos sem publicação ou comentário real; separar prontidão de código e prova de execução real.
