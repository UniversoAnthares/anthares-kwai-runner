# TikTok restore + identidade após correção do revision guard
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: 31e7b9b285b384fbd413faf6a8cdd85b4320eec1
SUPERSEDES: test-hub/findings/20261005-1933-tiktok-render-revision-guard-invalid.md

BASELINE_PROVEN: deploy f9ed83d7 contém restore OIDC delegado e /health prioriza RENDER_GIT_COMMIT; Render documenta RENDER_GIT_COMMIT como variável runtime oficial.
FAILED_AVOIDED: não usa WORKER_RUNTIME_REV obsoleto; workflow é Cloudflare-allowlisted; não chama publisher.
SUCCESS_SIGNAL: health revision=f9ed83d7... + bootstrapped=true + central_restored=true + TIKTOK_SESSION_AND_IDENTITY_PROVEN.
FAILURE_SIGNAL: com revisão exata ativa, restore autorizado prova ausência/erro ou session-test rejeita identidade.
TEST_VALIDITY: revisão divergente, 401/403 ou erro de harness => INVALID, não hipótese FAILED.

## Objetivo
Executar a primeira prova causal válida de restore central e identidade após eliminar os dois bugs de harness/restore.
