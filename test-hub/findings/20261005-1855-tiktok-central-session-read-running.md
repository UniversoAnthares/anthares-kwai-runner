# Probe somente-leitura do estado central TikTok
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37385518878
JOB: none
COMMIT: feee16aa44a35016fea5d54084a9f1cfbee483e7
SUPERSEDES: none

## Objetivo
Responder isoladamente se existe storage state TikTok no anthares-control, sem deploy, bootstrap, sessão ou publicação.

## Resultado
Run read-only 37385518878 criado sob lease tiktok-session/central-state-read. Solicita GitHub OIDC com audience exata do controlador e expõe somente HTTP/available/updated_at/contagens, nunca cookies.

## Evidência decisiva
Workflow tiktok-central-session-read.yml e trigger feee16aa; estado inicial queued.

## Consequência
Se CENTRAL_SESSION_AVAILABLE, corrigir apenas caminho Render->control. Se CENTRAL_SESSION_ABSENT, não insistir em restore: localizar/produzir uma fonte autenticada de sessão. Se PROBE_AUTH_INVALID, classificar harness/auth e corrigir allowlist, não a hipótese de persistência.
