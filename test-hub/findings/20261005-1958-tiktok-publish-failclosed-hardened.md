# TikTok publish fail-closed hardening
STATUS: PROVEN
AREA: tiktok
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: db77bb339fcd25fda542945265978d959eb56858
SUPERSEDES: none

## Objetivo
Endurecer a rota de publicação enquanto sessão está bloqueada.

## Resultado
Contrato estático validado: publish só executa em workflow_dispatch; push do probe executa somente session-restore-probe; endpoint de publicação usa Render canônico anthares-tiktok-render-rootless; antes de baixar mídia ou chamar /publish exige session-status ready_for_tiktok=true.

## Evidência decisiva
.github/workflows/tiktok-real-publish.yml em db77bb33 contém if github.event_name == workflow_dispatch no job publish, BASE rootless e TIKTOK_PUBLISH_PREFLIGHT fail-closed.

## Consequência
LEASE tiktok-publish encerrado. Não disparar canário até tiktok-session ficar PROVEN. Depois disso, usar exatamente um vídeo real e confirmar resultado antes de qualquer segundo publish. A durabilidade de dedupe entre redeploys ainda depende da fila/controlador central e não foi alterada por este chat.
