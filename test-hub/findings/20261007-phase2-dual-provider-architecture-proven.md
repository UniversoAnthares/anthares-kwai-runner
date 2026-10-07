# 2026-10-07 — Phase 2 dual-provider architecture proven

STATUS: PROVEN/PARTIAL
AREA: architecture/provider-router
DATE: 2026-10-07
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37675173709
JOB: 112976698070
COMMIT: f78dd4cac40e5202ef484f6b31b154ab70b4f8dc
SUPERSEDES: test-hub/findings/20261007-lease-phase2-dual-provider-architecture.md

## Objetivo

Implementar a arquitetura em que GitHub e GitLab são providers pares, com seleção dinâmica e failover controlado, sem transformar nenhum deles em autoridade permanente.

## Resultado

PROVEN na camada de política: `tools/provider_router.py` implementa:
- snapshots de saúde por provider;
- estados READY/BLOCKED_QUOTA/DOWN/AUTH_REQUIRED/UNKNOWN/BUSY;
- seleção alternada entre peers, sem preferência estrutural;
- lease de escrita único por operação;
- renovação do lease;
- lease_generation incrementado em failover;
- checkpoint repository/ref/commit;
- failover somente quando o provider atual deixa de estar READY;
- rejeição de failover quando o HEAD do destino diverge do checkpoint;
- bloqueio de execução quando nenhum provider está disponível.

A documentação operacional foi adicionada em `tools/DUAL_PROVIDER_ARCHITECTURE.md` e o README passou a registrar a arquitetura.

## Evidência decisiva

Workflow público `37675173709`, job `112976698070`:
- 6 testes executados;
- 6 passaram;
- `Ran 6 tests in 0.001s`;
- `OK`;
- conclusão do workflow: `success`.

Casos cobertos: alternância de providers, segundo escritor bloqueado, failover após BLOCKED_QUOTA, divergência de checkpoint, ausência de provider e expiração de lease.

## Limite atual

A política está implementada e testada no runner. A persistência/deploy dessa política dentro do Worker Cloudflare `anthares-control` deve reutilizar o lease/heartbeat/fencing já existente. O código-fonte desse Worker não está presente nos repositórios GitHub atualmente conectados, portanto não houve alteração do Worker nesta rodada.

## Consequência

O desenho de execução passa a ser provider-neutral. Quando a camada de controle for integrada ao Worker, GitHub e GitLab poderão ser escolhidos dinamicamente conforme health/quota/checkpoint, sem execução concorrente da mesma operação.
