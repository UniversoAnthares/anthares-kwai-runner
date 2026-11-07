# 07/08 — Controle de releases Cloudflare ARA Backup
STATUS: PARTIAL — CODE_READY; deploy existente preservado
AREA: operations/ara-backup-release-and-emergency
ITEMS: [4,8,16,18]
DATE: 2026-11-06
LEASE: lease-opt07-08-ara-backup-release-20261106.md — CLOSED
BASELINE_PROVEN: dois workflows diferentes implantam no mesmo Worker anthares-ara-backup; o stateless era ativado por push e tinha concorrencia diferente do stateful.
IMPLEMENTED:
- Workflow stateless agora executa deploy apenas por workflow_dispatch em main, exigindo release_sha SHA-40 exato.
- Fluxo de release normal exige igualdade com HEAD main; emergencia autoriza ancestral do main somente com incident_ref preenchido.
- Primeiro verifica se a mesma versao possui run anterior bem-sucedida E cabecalho de servico healthy; ignora rebuild repetido.
- Dois publicadores do Worker compartilham o mesmo concurrency group sem cancelamento de deploy em curso.
- Mantidos deploy via Wrangler existente, health e verificacao de cabecalho; nenhum segredo novo.
SUCCESS_SIGNAL: branch/PR integrada com dois workflows consistentes; proximo release explicitamente autorizado apresenta ARA_RELEASE_SHA_APPROVED ou SKIP/receipt de health.
FAILURE_SIGNAL: SHA divergente, incidente ausente, branch incorreta, API indisponivel ou lancamento concorrente — abortar antes do deploy.
TEST_VALIDITY: verificacao direcionada dos oito invariantes do YAML, sem rodar releases de prova.
COST_ADDED: R$0
PRODUCTION_EFFECT: nenhuma alteracao Worker agora; controle aplicado no proximo release manual autorizado.
SUPERSEDES: lease-opt07-08-ara-backup-release-20261106.md
