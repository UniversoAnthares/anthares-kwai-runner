# Lease renewal — WordPress QA multi-IA, runner failover e espelhos redundantes
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-09
RUN: GitLab pipeline 2930576949
JOB: wordpress_php_qa 17060518399
COMMIT: e383206b97ef50dda100f30f5e6b90f4d951d1c2
SUPERSEDES: test-hub/findings/20261009-1242-lease-wordpress-qa-redundancy.md

## Provas intermediárias
- GitLab pipeline 2930576949: SUCCESS, 6/6 jobs.
- PHP lint: 329 arquivos, 0 falhas.
- `ANTHARES_QA_REDUNDANCY_CONTRACT=PROVEN`.
- Runner GitLab executou de forma independente.
- Probe: `github_mirror=no qa_ssh=no`; esses dois caminhos permanecem fail-closed até terem credenciais no GitLab.
- Run GitHub 37891612002 classificado como falha pré-step de infraestrutura (`runner_id=0`, `steps=[]`).

## Lease
Holder: ChatGPT
Expires: 2026-10-09T13:40:00Z
Scope: anthares-wordpress QA/autofix/mirror redundancy only.
