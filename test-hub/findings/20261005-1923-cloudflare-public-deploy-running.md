# Public runner Cloudflare deploy sem dependência do runner privado
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: pending
JOB: cloudflare-central-deploy
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-1921-cloudflare-tiktok-read-private-deploy-invalid.md

BASELINE_PROVEN: controlador anthares-control existente; commit privado 8fa4187 contém a correção OIDC; runner público GitHub é PROVEN como infraestrutura remota.
FAILED_AVOIDED: deploy privado falha antes de execução útil; esta rodada usa runner público e snapshot exato do controlador, sem depender de runner privado.
SUCCESS_SIGNAL: Wrangler deploy conclui no runner público, /health responde anthares-control e probe tiktok-central-session-read deixa de receber 401.
FAILURE_SIGNAL: deploy público executa Wrangler contra o snapshot correto e é rejeitado por Cloudflare, ou após deploy confirmado o probe ainda recebe jwt_workflow/401.
TEST_VALIDITY: secret ausente, checkout/fetch quebrado, runner indisponível ou workflow não iniciado são falha de harness e não refutam OIDC.

## Objetivo
Publicar a versão corrigida do controlador por mecanismo causalmente diferente do runner privado.

## Consequência
Não abrir deploy Cloudflare concorrente enquanto este finding estiver RUNNING.
