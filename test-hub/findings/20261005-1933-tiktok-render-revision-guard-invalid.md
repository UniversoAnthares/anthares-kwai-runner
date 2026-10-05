# TikTok restore probe bloqueado por marcador de revisão obsoleto
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388273031
JOB: 112026953805
COMMIT: c7a84b8a44e440beedec9fe8baee7e887e6b34fc
SUPERSEDES: test-hub/findings/20261005-1930-tiktok-restore-identity-running.md

## Objetivo
Restaurar sessão central e validar identidade sem publicar.

## Resultado
INVALID/NOT_TESTED para sessão e identidade. O deploy fc26d51a ficou LIVE, mas /health continuou expondo revision=55b0d581 por WORKER_RUNTIME_REV obsoleto. O guard bloqueou o teste antes de tocar na sessão. O job publish ficou skipped.

## Evidência decisiva
Job 112026953805 repetiu render_revision=55b0d581 durante 40 probes e terminou RENDER_REVISION_NOT_READY. Render API confirmou deploy fc26d51a LIVE às 23:25:09Z.

## Consequência
Corrigir /health para usar RENDER_GIT_COMMIT como fonte primária de revisão; só então repetir. Não classificar sessão/identidade como FAILED.
