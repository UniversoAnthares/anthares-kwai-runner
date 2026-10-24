# Lease: CORTES offline role capability attestation gate
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
RUN: none
JOB: ChatGPT — isolate privileged role defaults in CI
COMMIT: 38e46519d010c6fb6786c400c39844675ef43e50
SUPERSEDES: none
LEASE_AREA: clipper-ci-neon-role-capability
LEASE_OWNER: ChatGPT current conversation
LEASE_START_UTC: 2026-10-24T17:17:00Z
LEASE_MAX_EXPIRY_UTC: 2026-10-24T17:42:00Z

## Objetivo
Corrigir na base de código ci/network_neon_isolation_audit.py do repositório Anthares Clipper a omissão de verificação de CREATE ROLE e CREATE DB, após evidência real de novos logins Neon QA provisionados com BYPASSRLS/CREATEROLE/CREATEDB.

## BASELINE_PROVEN
Clipper main SHA 7296299623d81236024e3cadbef734b0fd2c901d. Blob ci/network_neon_isolation_audit.py 3f96d3917b7770bb481709cbd589f1357cf5f02b e teste tests/test_network_neon_isolation_audit.py 719e7b15606c5f1d0875a6394f790b07a3f04015.
Neon branch QA br-quiet-unit-b8w1tqmf produziu duas roles LOGIN com bypassrls=true, createrole=true e createdb=true via API nativa; tentativa ALTER ROLE foi negada, e as duas roles criadas nessa rodada foram eliminadas com readback no catálogo. Roles NOLOGIN originais continuam sem bypass, CREATEDB/CREATEROLE e sem permissão no ledger real.
O lease simultâneo test-hub/findings/20261024-1704-lease-cortes-neon-qa-runtime-health.md diz respeito ao runtime health QA e não autoriza esta tarefa a modificar a branch QA ou efetuar deploy.

## FAILED_AVOIDED
Não tocar funções/Neon branch QA devido a lease existente. Não criar novas roles nem escrever produção SQL; não executar os testes de workspace/export/release candidate previamente recusados. Não contornar recusa remota Windows anterior por outro canal. Não alterar código de publicador ou regras de outra rede.

## SUCCESS_SIGNAL
PR de plataforma limitando mudanças a auditor SQL offline e respectivos testes, acrescentando rejeição explícita a role.can_create_role / can_create_database (false exigido). Regressões reais, hashes/commits confirmados e merge somente após validação confiável; auditoria nunca autoriza deploy.

## FAILURE_SIGNAL
SHA de main/blobs alterados por outro agente, não aprovação dos testes, acesso a dados privados ou execução de publicador, erro de check que permita role superprivilegiada.

## TEST_VALIDITY
Teste sintético executável confirma contrato do gate, não comprova roles LOGIN independentes, políticas/ACL produtivas nem implantação real. Falha de runner/quota é inválida como prova de software. Nenhum pedido de segurança recusado pode ser reexecutado por outro ambiente.

## Consequência
Lease máximo 25 minutos; fechar por novo finding append-only com evidence and SUPERSEDES. Não promover CI code patch como autorização de cutover.
