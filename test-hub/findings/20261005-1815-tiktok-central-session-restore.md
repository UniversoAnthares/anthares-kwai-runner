# Sessão TikTok perdida no restart; restore central ausente
STATUS: FAILED
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380633499
JOB: 112001397701
COMMIT: cdd656b50abe002d2d607def6d8496d616033693
SUPERSEDES: none

## Objetivo
Explicar bootstrapped=false após corrigir OIDC e preservar a arquitetura remota já existente.

## Resultado
O código já possui render_session.py para persistir storage state no anthares-control em /tiktok/session-state, mas service.py mantinha STATE em /tmp e não restaurava o estado central após restart/deploy. Foi adicionada restauração central antes de session-status declarar a sessão ausente.

## Evidência decisiva
Run 37380633499: OIDC passou, porém session-status retornou bootstrapped=false. Inspeção do código mostrou persist_session_state() enviando cookies/origins ao controlador, enquanto service.py não tinha caminho de leitura correspondente.

## Consequência
Não criar segundo storage nem voltar a estado local. Usar anthares-control como fonte durável e validar a leitura após deploy. Commit corretivo cdd656b50abe002d2d607def6d8496d616033693. O disparo automático do deploy foi bloqueado pela camada de segurança da ferramenta nesta tentativa; não interpretar isso como falha do código.
