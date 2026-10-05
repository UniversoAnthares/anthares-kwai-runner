# OIDC público corrigido; sessão Render perdida após deploy
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37380633499
JOB: 112001397813, 112001397701, 112001397656, 112001397649, 112001397707, 112001397346
COMMIT: ed9787ea606ef24a3c1bf0891721d49b54916245
SUPERSEDES: test-hub/findings/20261005-1809-tiktok-workflowref-retest.md

## Objetivo
Validar a correção workflow_ref e identificar a próxima barreira real do publicador TikTok remoto.

## Resultado
OIDC está PROVEN: job 02 autenticou no Render e /session-status retornou ok=true. A sessão TikTok, porém, não sobreviveu ao deploy: bootstrapped=false, identity_verified=false, ready_for_tiktok=false. Os dry-runs 08/09/10 falharam 409 session not bootstrapped; não são falhas dos dry-runs.

## Evidência decisiva
Job 112001397813: {"bootstrapped": false, "identity_verified": false, "ok": true, "ready_for_tiktok": false} e PASS focused-02. Job 112001397701 confirmou o mesmo estado. Jobs 08/09/10 retornaram HTTP 409 {"error":"session not bootstrapped"}.

## Consequência
Não alterar mais OIDC sem nova evidência. Não repetir dry-runs antes de restaurar persistência. Investigar e reutilizar a persistência central de sessão já existente; /tmp não pode ser a fonte durável.
