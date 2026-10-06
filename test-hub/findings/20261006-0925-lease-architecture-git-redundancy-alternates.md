# Lease — alternate Git redundancy completion paths
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Fechar GitLab e Codeberg/Forgejo por rotas independentes da autorização originalmente bloqueada, incluindo identidades existentes, Forgejo autohospedado e MCP/API próprios.

## Lease
OWNER: chatgpt-git-provider-redundancy
EXPIRES: 2026-10-06T13:55:00Z
SCOPE: git provider redundancy only.

## BASELINE_PROVEN
Workflow fail-closed, SHA checker e failover layer já existem; run 37465604828 comprovou AUTH_REQUIRED para os destinos ausentes.

## FAILED_AVOIDED
Não repetir mirror sem target/credencial. Não depender do PC em produção. Não usar cascata entre provedores. Não gravar credenciais.

## SUCCESS_SIGNAL
Obter pelo menos um destino Forgejo/Codeberg real e persistente com clone/push/API; avançar GitLab por identidade/OAuth/API existente; registrar provas reais.

## FAILURE_SIGNAL
Toda infraestrutura cloud persistente disponível exigir identidade humana ainda inexistente ou armazenamento incompatível.

## TEST_VALIDITY
Reler HEAD após lease; ceder a lease architecture anterior conflitante ainda ativo.
