# Snapshot Cloudflare atual compila no Wrangler com bindings corretos
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: local-readonly-wrangler-dryrun
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2016-cloudflare-local-oauth-deploy-path-proven.md
FAILED_AVOIDED: não executar deploy durante lease cloudflare-control; não depender do GitHub secret ausente; não alterar Worker/KV/DO.
SUCCESS_SIGNAL: Wrangler empacota o HEAD atual em dry-run e reconhece bindings do Durable Object e KV.
FAILURE_SIGNAL: erro de bundle/config/migration/binding antes de upload.
TEST_VALIDITY: clone limpo do HEAD público; `wrangler deploy --dry-run`; nenhum upload/deploy foi realizado.

## Objetivo
Validar que o snapshot que pretendemos implantar é aceito pelo mesmo Wrangler autenticado disponível para o deploy, antes de tocar produção.

## Resultado
PROVEN. `wrangler@4.43.0 deploy --dry-run` empacotou o Worker com sucesso. O bundle teve 43.35 KiB (gzip 10.47 KiB). Wrangler reconheceu `env.ANTHARES_QUEUE (AntharesQueue)` como Durable Object e `env.ANTHARES_STATE` como KV Namespace e encerrou explicitamente em modo dry-run.

## Evidência decisiva
Saída: `Your Worker has access to the following bindings`, seguida de `env.ANTHARES_QUEUE (AntharesQueue) Durable Object`, `env.ANTHARES_STATE (...) KV Namespace`, e `--dry-run: exiting now.`

## Consequência
O próximo deploy real, após liberação do lease e releitura do HEAD, já não está bloqueado por bundle/configuração Wrangler. Continua obrigatório validar que o HEAD a implantar é o snapshot endurecido e verificar `/health`, `/strategy`, `/failover-self-test`, queue self-test e ausência de fallback local depois do deploy.