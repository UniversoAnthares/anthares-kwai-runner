# Restore central falhou por autenticação incompatível
STATUS: FAILED
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37383338240
JOB: 112010497762,112010498089
COMMIT: 74dd01f21b7c4907d0bce75f0fb0c13374efc883
SUPERSEDES: test-hub/findings/20261005-1835-tiktok-central-restore-retest.md

## Objetivo
Identificar por que cdd656b5 não restaurou a sessão central.

## Resultado
OIDC Render continua PROVEN, mas central_restored=false. A causa de código é incompatibilidade de autenticação: GET /tiktok/session-state no Cloudflare aceita GitHub OIDC; cdd656b5 tentou ANTHARES_CONTROL_TOKEN. A escrita já usa assinatura RSA ou OIDC. Restore alterado para usar ANTHARES_CONTROL_OIDC_TOKEN delegado, alinhando-o ao contrato real do Worker.

## Evidência decisiva
Job 112010497762: ok=true, central_restored=false, bootstrapped=false. Worker cloudflare-worker/src/index.js exige verifyGithubOidc no GET /tiktok/session-state. Commit corretivo 74dd01f21b7c4907d0bce75f0fb0c13374efc883.

## Consequência
Não repetir restore com ANTHARES_CONTROL_TOKEN. Próximo teste precisa prover OIDC delegado válido ao Render ou mover o GET para autenticação Render assinada; validar separadamente presença do estado central e autorização de leitura antes dos dry-runs.
