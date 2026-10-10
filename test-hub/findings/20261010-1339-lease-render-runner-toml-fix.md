# Render GitLab QA runner TOML regression — lease
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38072415131
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38072415131/job/114272385137
COMMIT: 0b4661fa234daabbb7e7c2681942fc2a669f0cf9
SUPERSEDES: none
LEASE_AREA: render-runner
LEASE_OWNER: infra-automation-20261010-1339-CDT
LEASE_EXPIRES_UTC: 2026-10-10T18:08:00Z

## Objetivo
Corrigir a geração de config.toml do runner Render custom executor, após PR #20 ter introduzido caracteres literais \\n em vez de quebras de linha TOML. Não alterar runner remoto nem credenciais antes de teste e revisão.

## Baseline e concorrência
BASELINE_PROVEN: runner-source, custom-executor-source, source-compile, checkout-isolation aprovados no run 38072415131. PR #20 foi merged 17:36:15Z; serviço Render está com autoDeploy=no e último deploy registrado às 15:40:41Z.
FAILED_AVOIDED: diagnósticos repetidos de GitLab API e health sem mudança causal; correção focal somente no serializador TOML.
SUCCESS_SIGNAL: teste de regressão com tomllib valida configuração e runner continua com concorrência 1, config_exec e config_args; CI do commit de correção confirma os testes.
FAILURE_SIGNAL: TOML inválido ou falha de testes unitários após correção.
TEST_VALIDITY: verificar código-fonte exato do commit e testar função de patch com fixture de TOML de registro; falha de autenticação, quota ou rede não invalida teste local.

## Plano
Criar branch isolada, corrigir somente literais \\n, adicionar regressão e abrir PR. Evitar deploy até evidência de validação.
