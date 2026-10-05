# OIDC público continuou 401 após deploy atual
STATUS: FAILED
AREA: tiktok
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378729369
JOB: 111994756820
COMMIT: facc9b79e9e04e32d2c476ff0515529b7a35b885
SUPERSEDES: test-hub/findings/20261005-1748-tiktok-render-deploy-antigo.md

## Objetivo
Confirmar se colocar a revisão atual do Render em produção eliminaria o 401 dos probes OIDC do repositório público.

## Resultado
Não eliminou. O probe 02 OIDC public runner -> Render recebeu HTTP 401 após o deploy Render estar live. Os probes 04, 08, 09 e 10 também receberam o mesmo 401 e portanto não chegaram a testar sessão ou dry-run.

## Evidência decisiva
Job 111994756820: HTTP 401 {"error":"unauthorized"} em /session-status. O mesmo padrão ocorreu nos jobs 111994756708, 111994756392, 111994756799 e 111994756720. O código do Render ainda usava allowlist exata de job_workflow_ref e não incluía tiktok-postdeploy-focused.yml.

## Consequência
A hipótese de que o 401 era apenas revisão antiga está superada. Não repetir a mesma allowlist exata. Próxima tentativa deve mudar a causa: autorizar de forma restrita qualquer workflow do repositório público anthares-kwai-runner somente em refs/heads/main, mantendo validação criptográfica do OIDC, repository, ref, issuer, audience e event_name.
