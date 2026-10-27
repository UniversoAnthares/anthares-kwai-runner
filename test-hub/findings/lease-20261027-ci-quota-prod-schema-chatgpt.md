# Lease — Implantação aditiva do ledger CI de cota no Neon principal
STATUS: RUNNING
AREA: architecture / ci-quota-prod-schema
DATE: 2026-10-27
RUN: none
JOB: Neon project purple-flower-35918989, branch br-crimson-unit-b89nau08
COMMIT: 094da7ea1b0598837c9bd76c98b5ea8eeb52d356
SUPERSEDES: none

## Proprietário / escopo
ChatGPT, somente criação da tabela ainda ausente public.anthares_ci_quota_attempts e índice com migração versionada da PR #1522. Não ativar trabalhador, conceder permissões amplas, alterar publicadores ou cancelar jobs compartilhados. Lease válido até 30 minutos após este commit.

BASELINE_PROVEN: tabela ausente na consulta Neon principal; QA rollback na branch br-silent-mud-b8fzvqta comprovou contrato PostgreSQL; PRs #1522/#1525 integradas.
FAILED_AVOIDED: nenhuma migração destrutiva, nenhum DROP, overwrite ou mudança de tabelas existentes.
SUCCESS_SIGNAL: tabela e índice presentes no banco principal, restrição de owner/generation confirmada por catálogo; nenhuma linha nova de execução.
FAILURE_SIGNAL: conflito com objeto preexistente/incompatível, grant inesperado ou schema drift; interromper a mutação.
TEST_VALIDITY: observação do catálogo após DDL, sem execuções simuladas nem publicação.
