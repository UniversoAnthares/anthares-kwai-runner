# Lease — GitLab and Codeberg/Forgejo redundancy
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Integrar GitLab e Codeberg/Forgejo como redundâncias independentes do GitHub, com sincronização, CI mínimo, verificação de SHA, failover e acesso por agentes.

## Lease
OWNER: chatgpt-git-provider-redundancy
EXPIRES: 2026-10-06T13:28:00Z
SCOPE: GitLab, Codeberg/Forgejo, provider mirrors, cross-provider SHA checker, failover docs/tests e MCP/API wrappers relacionados.

## BASELINE_PROVEN
GitHub permanece principal; Test Hub e arsenal health estão PROVEN. O repositório anthares-kwai-runner já contém .gitlab-ci.yml/provider-smoke, porém test-hub/ARSENAL.md classifica GitLab e Codeberg/Forgejo como NOT_STARTED.

## FAILED_AVOIDED
Nenhuma credencial será gravada em commits/findings/logs. Não usar PC como runtime de produção. Não criar cascata GitHub→GitLab→Codeberg. Não promover criação de repositório isolada a PROVEN.

## SUCCESS_SIGNAL
Mirrors independentes recebem SHA/branches/tags; clone funciona; GitLab CI mínimo passa; acesso de agente lê/escreve; checker compara SHAs; failover é testado sem merge destrutivo.

## FAILURE_SIGNAL
Ausência de identidade/credencial/autorização nos provedores após concluir toda preparação independente, ou incompatibilidade comprovada do plano gratuito/API.

## TEST_VALIDITY
Reler HEAD e leases architecture antes de mutações. Se surgir lease architecture anterior conflitante ou baseline mudar, invalidar a mutação e registrar finding novo.
