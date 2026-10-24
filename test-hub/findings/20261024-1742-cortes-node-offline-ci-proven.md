# CORTES queue Node contracts — CI read-only executada e lease encerrado
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40117175936
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40117175936/job/120940745593
COMMIT: 21ffada8d4497dfd29952914e09ab8f7b856b68d
SUPERSEDES: test-hub/findings/20261024-1741-lease-cortes-queue-node-contracts-ci.md
LEASE_AREA: cortes-queue-node-offline-ci
LEASE_STATUS: CLOSED

## Objetivo
Executar suíte Node/JS do contrato de health da fila, encaminhamento Cloudflare e rejeição de operações anônimas, sem alterar publicadores, dados, filas ou credenciais.

## BASELINE_PROVEN
PR #1316 de CI Node criada com apenas workflow read-only .github/workflows/cortes-queue-node-readonly-ci.yml e finding de lease. Source JS da PR #1303 na main; sem redeploy da função Neon produtiva deployment 39 em leitura anterior. Escopo separado de lease Neon QA runtime health.

## FAILED_AVOIDED
Sem token OIDC ou secrets, sem GET/POST de API remota de publicação, sem requeue, worker deployment, role SQL, WP, computador Windows ou agente externo. Runners hospedados somente para mocks definidos. Nenhuma suíte anteriormente recusada por segurança foi reexecutada.

## SUCCESS_SIGNAL
GitHub Actions run 40117175936 completed/success, head SHA a023936272e2801dcbdfd191c9ef539924c1aeab, Node v22.23.3; node --check de infra/neon-cortes-queue/index.mjs, infra/cloudflare-cortes-queue-ha/src/index.js e tests/test_cortes_queue_ha.mjs concluídos. node --test tests/test_cortes_queue_ha.mjs: 6 testes, 6 pass, 0 fail, 0 skipped no log do job 120940745593. Checks: health network_isolation=false, rejeição de enqueue sem OIDC, endpoints desconhecidos, proxy health, edge sem mutação anônima e preservação de token em rota fixa. PR #1316 merged na main em 21ffada8d4497dfd29952914e09ab8f7b856b68d; nenhum publicador modificado.

## FAILURE_SIGNAL
CI sem runner ou com problema de faturamento seria NOT_TESTED; testes falhos seriam FAILED. Evidência atingiu steps esperados e PASS, logo PROVEN somente nos contratos offline.

## TEST_VALIDITY
Teste usa mocks. NÃO valida código Neon deployado, recibo HTTP produtivo, RLS de produção, escritor único, confirmação de postagem, atestação editorial externa, canário ou rollback. Não executou operação remota Windows previamente negada.

## Consequência
Lease encerrado. CI Node de contrato resolvido; item 16 ainda inclui rollout seguro do health Neon e verificação HTTP/rollback separado. Implantação exige novo lease e controle de produção.
