# TikTok public rehydrate failed at control OIDC audience, before Render mutation
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394851557
JOB: 112048264996
COMMIT: 1547540745107da9ad827ca962469b2c9056fd6b
SUPERSEDES: none

BASELINE_PROVEN: run 37394495580 proved production v12 GET /tiktok/session-state with GitHub OIDC and 21 cookies.
FAILED_AVOIDED: public runner used; no private Actions allocation dependency.
SUCCESS_SIGNAL: central load -> Render bootstrap -> session-status -> identity_verified -> refreshed central persist.
FAILURE_SIGNAL: valid authenticated request reaches a causal endpoint and fails.
TEST_VALIDITY: the control read must reproduce the already-proven OIDC contract before any Render mutation.

## Resultado
O workflow falhou no primeiro GET /tiktok/session-state com HTTP 401. Nenhum bootstrap Render ocorreu. Isto contradiz a baseline 37394495580 e portanto invalida o teste de rehydrate; não é evidência contra a sessão nem contra o Render.

## Evidência decisiva
O workflow gera control_token com audience igual ao URL completo do Worker (`oidc(control)`), enquanto o probe PROVEN usa audience URL-encoded no contrato aceito pelo Worker. Job 112048264996 morreu em `HTTP 401 on session-state` antes de imprimir CENTRAL_SESSION_LOAD=OK.

## Consequência
Corrigir/reutilizar literalmente o contrato OIDC do workflow PROVEN 37394495580 antes de repetir rehydrate. Não tocar sessão/Render até o preflight reproduzir HTTP 200 available=true. Classificar 37394851557 como harness/auth-contract invalid, não como falha de rehydration.