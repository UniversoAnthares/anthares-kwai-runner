# Lease de manutenção: CORTES migração cloud de mídia
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-23
RUN: none — GitHub Actions excluído pelo titular
JOB: ChatGPT/cortes-cloud-migration-continue-20261023
COMMIT: anthares-clipper/0d999552e1887ac18b7c5ab0418b7020c074b230
SUPERSEDES: none
LEASE_OWNER: ChatGPT
LEASE_SCOPE: feature/cortes-cloud-drive-replication-20261023 — novos módulos do produtor, armazenamento e testes, sem alterar publicadores sociais
LEASE_DURATION: máximo 30 minutos a contar deste commit; renovação requer novo finding

## BASELINE_PROVEN
34 testes, 33 aprovados/1 ignorado, de replicação, limpeza fail-closed e prioridade de executores externos. Produção permanece em Windows; OAuth Drive dedicado e workers externos sem comprovação.

## FAILED_AVOIDED
Falha do render Windows por capacidade D: menor que 8GiB; evitar rodar outra live no PC. GitLab ci_quota_exceeded; não executar pipelines. Google OAuth compartilhado atingiu 403 rateLimitExceeded; preservar configuração e não forçar uploads.

## SUCCESS_SIGNAL
Commit de staging com testes offline, sem lançamento de GitHub Actions, rede social, publicação nem exclusão de mídia. Contrato do worker cloud e integração futura documentados.

## FAILURE_SIGNAL
SHA base alterado, testes falhos, segredo ausente, concorrência no mesmo escopo ou indisponibilidade real do worker.

## TEST_VALIDITY
Verificar branch SHA e comparar com main; jobs de publicação continuam intocados.
