# WordPress authenticated smoke: offload from Windows to public GitHub-hosted executor
STATUS: RUNNING
AREA: wordpress-auth-smoke/cloud-offload
DATE: 2026-10-29
RUN: none
JOB: none
COMMIT: d25757fadec1ccaa00e7a9f851ce10027c90d3e1
SUPERSEDES: none
LEASE_OWNER: chatgpt-cloud-offload-wordpress-smoke-20261029
LEASE_EXPIRES_UTC: 2026-10-29T17:42:38.421Z

BASELINE_PROVEN: workflow .github/workflows/cortes-wordpress-auth-smoke.yml executa read-only HTTPS GET via tools/cortes_wp_auth_smoke.py (somente stdlib) em qa-p0-independent Windows. Baseline run 40500306462 (27/10/2026) falhou com CORTES_WP_AUTH_SMOKE=AUTH_MISSING, sem efeito no WordPress. GitHub-hosted ubuntu-24.04 já foi comprovado no repositório público com run 40913166690 e outras execuções.
FAILED_AVOIDED: nenhuma autenticação nova, conta alterada, publicação ou bypass de política. Manter falha explícita se secrets continuarem indisponíveis.
SUCCESS_SIGNAL: executor GitHub Actions Ubuntu provisionado e script de QA somente leitura realmente executado fora do PC. Validação HTTP 200 é gate funcional separado, dependente das credenciais.
FAILURE_SIGNAL: erro de alocação/no-steps, problema novo de linguagem ou plataforma; não promover.
TEST_VALIDITY: runner sem steps => NOT_TESTED/HARNESS; AUTH_MISSING preexistente => migração de execução possível, autenticação não comprovada.
PEER: GitLab main contém workflow Windows equivalente. Sem espelhamento cego.
