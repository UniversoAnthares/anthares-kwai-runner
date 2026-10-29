# X legado: inventário de ledger em executor hospedado
STATUS: RUNNING
AREA: x-ledger-inventory/cloud-offload
DATE: 2026-10-29
RUN: none
JOB: none
COMMIT: 376746e8b7f406715e1f2857c811902abee1ed8e
SUPERSEDES: none
LEASE_OWNER: chatgpt-cloud-offload-20261029
LEASE_EXPIRES_UTC: 2026-10-29T17:00:25.049Z

BASELINE_PROVEN: O workflow .github/workflows/x-legacy-ledger-inventory.yml usa Windows self-hosted, mas tools/x_legacy_ledger_inventory.py apenas consulta a API GitHub e o endpoint remoto do ledger. O runner GitHub-hosted ubuntu-24.04 executou neste repositório com sucesso em 29/10/2026 (run 40911046077).
FAILED_AVOIDED: preservar execução e dados produtivos; alterar somente um job de inventário read-only. Nenhuma publicação, mutação de fila ou cópia de credencial.
SUCCESS_SIGNAL: novo run do workflow alocado em ubuntu-24.04, com runner_name GitHub Actions, steps completos e sucesso real do inventário.
FAILURE_SIGNAL: falha de alocação, autenticação ou script; corrigir ou reverter, distinguindo erro de harness.
TEST_VALIDITY: se nenhum step começar, classificar NOT_TESTED/HARNESS.
SCOPE: workflow x-legacy-ledger-inventory.yml; preservar github token e secret no GitHub Actions, sem expô-los.
