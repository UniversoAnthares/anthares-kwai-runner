# CI-01 / CORTES credential workflow scope — lease
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-25
RUN: none
JOB: ci01-credrefs-20261025
COMMIT: db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: none
LEASE_AREA: ci01-credential-scope-offline
LEASE_OWNER: ChatGPT Anthares Operations
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
A auditoria de referências de secrets já existe e a suíte `tests/test_network_workflow_credential_audit.py` está incluída entre as quinze suites permitidas no workflow manual network-offline-regressions.yml. Suíte composta de 12 testes com entradas sintéticas.

## FAILED_AVOIDED
Executar só essa suíte permitida; nenhuma das quatro suites explicitamente excluídas. Não ler secrets reais, rodar publicadores, alterar sistemas ou fazer deploy. GitLab main divergente, sem espelhamento.

## SUCCESS_SIGNAL
Gatilho dedicado por PR e push no main, teste 12/12 PASS em runner real autorizado, recibo, log e readback da main após merge.

## FAILURE_SIGNAL
Sem runner/steps => NOT_TESTED; teste falho => FAILED, sem merge; falta de prova de artefato => PARCIAL. Não substituir gate IAM/branch protection.

## TEST_VALIDITY
Teste de referências declaradas no YAML e contrato offline. Mesmo verde não comprova isolamento efetivo de credenciais, identidades, secrets ou ACL no provedor e nunca autoriza publicação.
