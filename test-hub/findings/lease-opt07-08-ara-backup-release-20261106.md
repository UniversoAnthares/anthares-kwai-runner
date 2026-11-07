# Plano 07/08 — lease de releases ARA Cloudflare
STATUS: RUNNING
AREA: operations/ara-backup-release-and-emergency
ITEMS: [4,8,16,18]
OWNER: ChatGPT reestruturacao 2026-11-06
BASE_HEAD: 85e57b6af4cda5cc6f143076be892acdabb0d582
GOVERNANCE: 223433740e807a90
SCOPE: .github/workflows/ara-backup-stateless-proxy-deploy.yml; .github/workflows/cloudflare-ara-backup-deploy.yml
BASELINE_PROVEN: stateless deploy por push e dispatch; stateful deploy manual pode sobrescrever o mesmo Worker; grupos de concorrencia distintos.
FAILED_AVOIDED: nenhum deploy de prova, teste de midia, alteracao de token ou runtime, custo novo ou PC runner.
SUCCESS_SIGNAL: apenas release explicitamente aprovado por SHA; emergencia manual com incidente; bloqueio unico para o mesmo Worker; release repetida e saudavel ignorada.
FAILURE_SIGNAL: HEAD mudou, conflito de lease, deploy sem SHA ou colisao com publicador.
TEST_VALIDITY: revisao YAML dirigida; nenhuma publicacao de producao neste PR.
ROLLBACK: revert PR e preservar release aplicada.
COST_ADDED: R$0
LEASE: expires after 30 minutes; close in final finding.
