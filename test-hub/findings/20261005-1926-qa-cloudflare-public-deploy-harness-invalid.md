# Public Cloudflare deploy did not reach Wrangler
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37387933513
JOB: 112025850322
COMMIT: 5c78ecbc32a2c57fad11212cc82000a305916d88
SUPERSEDES: test-hub/findings/20261005-1923-cloudflare-public-deploy-running.md

BASELINE_PROVEN: snapshot validation passed and contains the intended TikTok workflow allowlist change.
FAILED_AVOIDED: private-runner failure was avoided by moving execution to the public runner.
SUCCESS_SIGNAL: Wrangler deploy completes and authenticated TikTok central read stops returning jwt_workflow/401.
FAILURE_SIGNAL: Wrangler actually executes against the intended snapshot and Cloudflare rejects it, or deployed code still returns jwt_workflow.
TEST_VALIDITY: CLOUDFLARE_API_TOKEN must be present; Wrangler must execute.

## Objetivo
Auditar o deploy público declarado RUNNING.

## Resultado
TEST INVALID para a hipótese de deploy/OIDC. O runner público funcionou e o snapshot correto foi validado, mas o secret CLOUDFLARE_API_TOKEN chegou vazio e o step encerrou em `test -n "$CLOUDFLARE_API_TOKEN"` antes de Wrangler.

## Evidência decisiva
Job 112025850322: `SNAPSHOT_VALID=8fa4187...`; em seguida environment mostra `CLOUDFLARE_API_TOKEN:` vazio e o step termina exit 1 antes de `npx wrangler deploy`.

## Consequência
CHAT 4 não deve repetir o mesmo run sem mudança causal de credencial/contrato de deploy. A correção OIDC continua IMPLEMENTED, não DEPLOYED/PROVEN. O runner público em si não falhou.