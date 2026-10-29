# Instagram Graph: remove read-only auth check from Windows executor
STATUS: RUNNING
AREA: instagram-graph-preflight/cloud-offload
DATE: 2026-10-29
RUN: none
JOB: none
COMMIT: 3a54b45e97e0e71025fe5f771997e0d3ac84e64f
SUPERSEDES: none
LEASE_OWNER: chatgpt-cloud-offload-instagram-20261029
LEASE_EXPIRES_UTC: 2026-10-29T17:06:53.250Z

BASELINE_PROVEN: scripts/instagram_publish.py usa Python stdlib e chamadas HTTPS oficiais, com fluxo read-only. Workflow atual executa em Windows self-hosted por dependência exclusiva de caminho local do Python. O runner ubuntu-24.04 público já tem prova real de disponibilidade.
FAILED_AVOIDED: remover somente runtime Windows; manter API, identidade e escopo read-only. Sem publicação, alteração de acesso, cópia de token, alteração de conta ou fila.
SUCCESS_SIGNAL: workflow em GitHub-hosted ubuntu-24.04, prova de identidade oficial retornando saída 0; nenhuma execução local.
FAILURE_SIGNAL: credenciais ausentes, API rejeitada ou problema de execução, sem promoção e com status PARTIAL.
TEST_VALIDITY: falha antes de executar o step deve ser rotulada NOT_TESTED/HARNESS.
SCOPE: .github/workflows/cortes-instagram-graph-auth-preflight.yml; ambiente é GitHub Actions.
