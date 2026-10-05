# Lease TikTok session: provar estado central antes de novo deploy
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
LEASE: tiktok-session/central-state-read
BASELINE_COMMIT: 74dd01f21b7c4907d0bce75f0fb0c13374efc883
BASELINE_PROVEN: OIDC GitHub->Render PROVEN no run 37383338240; Render cdd656b5 live; central_restored=false.
FAILED_AVOIDED: não repetir restore com ANTHARES_CONTROL_TOKEN; não executar dry-runs antes de provar disponibilidade/leitura central; não inferir commit como deployado.
SUCCESS_SIGNAL: controlador responde available=true a leitura autenticada e Render restaura bootstrapped=true após revisão compatível.
FAILURE_SIGNAL: leitura autenticada responde available=false/404 ou autorização falha com motivo observável.
TEST_VALIDITY: probe deve obter OIDC válido para audience do anthares-control; falha do harness/OIDC não conta como ausência de sessão.
EXPIRES_AT: 2026-10-05T23:19:00Z
RUN: none
JOB: none
COMMIT: 74dd01f21b7c4907d0bce75f0fb0c13374efc883
SUPERSEDES: none

## Objetivo
Serializar qualquer mutação de tiktok-session e provar primeiro o estado central com diagnóstico somente-leitura.

## Resultado
Lease adquirido após snapshot de findings/runs; não havia lease TikTok nem run TikTok ativo.

## Evidência decisiva
Hub atualizado e somente Kwai State Driver Matrix estava RUNNING; runs TikTok anteriores estavam completed.

## Consequência
Nenhum novo deploy/session mutation TikTok até concluir este lease. Probes somente-leitura são permitidos.
