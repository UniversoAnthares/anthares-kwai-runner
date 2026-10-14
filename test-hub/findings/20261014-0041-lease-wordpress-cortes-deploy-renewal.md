# Lease renewal — deploy CORTES WordPress
STATUS: RUNNING
AREA: wordpress-deploy
DATE: 2026-10-14
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2944724371
JOB: wordpress_runtime_failover
COMMIT: none
SUPERSEDES: test-hub/findings/20261014-0014-lease-wordpress-cortes-deploy.md
OWNER: chatgpt-cortes-finalization
LEASE_START_UTC: 2026-10-14T00:41:00Z
LEASE_EXPIRES_UTC: 2026-10-14T01:11:00Z

## Objetivo
Concluir publicação e validação do plugin CORTES no WordPress real e restaurar os harnesses temporários.

## BASELINE_PROVEN
O wake público do Render foi reexecutado e emitiu `RENDER_GITLAB_RUNNER_REACHABLE=PROVEN`; os logs do Render mostram runner registrado e `gitlab-runner run` ativo. O pipeline GitLab 2944724371 permanece pendente nos jobs `render-qa`, portanto o caminho de tag atual não está sendo adquirido pelo runner recém-registrado.

## FAILED_AVOIDED
Não reconstruir Render (minutos gratuitos esgotados). Não depender de PC/ARA offline. Não repetir espera passiva pelo job `render-qa` sem alteração causal.

## SUCCESS_SIGNAL
Job GitLab alcança Hostinger, aplica exatamente o SHA GitHub 2761fda6c894fb4e0aa83baf1a5e4e1b98d85ca5, passa lint e emite `CORTES_LIVE_DEPLOY=PROVEN` e `DEPLOY_SHA=2761fda6c894fb4e0aa83baf1a5e4e1b98d85ca5`; em seguida harness temporário é restaurado.

## FAILURE_SIGNAL
SSH falha, lint falha, SHA diverge, WP-CLI não carrega CORTES ou runner não adquire nem job sem tag.

## TEST_VALIDITY
Falha antes de runner/SSH é infraestrutura e não refuta o plugin. Nenhuma publicação social é executada nesta validação.
