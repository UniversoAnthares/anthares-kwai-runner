# Lease — CI Node read-only da fila CORTES
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
RUN: pending GitHub Actions PR
JOB: ChatGPT CI bounded Node contracts
COMMIT: 0838a8e8ec9e72a66007830dcd80325fc5895a6e
SUPERSEDES: none
LEASE_AREA: cortes-queue-node-offline-ci
LEASE_OWNER: ChatGPT
LEASE_START_UTC: 2026-10-24T17:41:00Z
LEASE_MAX_EXPIRY_UTC: 2026-10-24T18:10:00Z

## Objetivo
Executar contrato Node já existente tests/test_cortes_queue_ha.mjs contra fonte atual infra/neon-cortes-queue/index.mjs e edge infra/cloudflare-cortes-queue-ha/src/index.js em GitHub Actions sem dados externos.

## BASELINE_PROVEN
A PR #1303 foi integrada, source health agora indica network_isolation:false e rls_attested:false no GitHub. Neon PROD cortesqueue deployment=39 ainda antigo. O lease anterior qa-cortes-neon-health-runtime registrado em finding 20261024-1704 é independente; não executar deploy nem interagir com essa instância.

## FAILED_AVOIDED
Não invocar Neon/Cloudflare remoto, OIDC, credenciais, mídia, WordPress ou jobs reais. Não repetir testes de CI de workspace que foram recusados anteriormente. Evitar alteração de YAML do HA que dispare deploy. Não depender da conta Windows bloqueada. Preservar os publicadores e a fila.

## SUCCESS_SIGNAL
GitHub Actions read-only, check syntax JS e node --test tests/test_cortes_queue_ha.mjs, com resultado de CI concluído SUCCESS e número de testes evidenciado em log; nenhum arquivo de publicador modificado nem deploy efetuado.

## FAILURE_SIGNAL
Runner sem capacidade/cota, erro de syntax/runtime, testes falhos ou nenhum run disparado. Se não atingir o step Node, classificar NOT_TESTED/infra e não aprovar software.

## TEST_VALIDITY
Contrato Node usa mocks de fetch e valores sintéticos. CI verde não valida conexão SQL, não implica health corrigido em Neon PROD, não comprova escritor único, recibos editoriais ou canário de publicação.

## Consequência
Fechar lease com finding SUPERSEDES ao concluir. Não tornar CI Node um deploy gate até branch protection e controle de identidade comprovados.
