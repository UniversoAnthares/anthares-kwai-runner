# Controle de release ARA — rota stateful
STATUS: RUNNING
AREA: operations/ara-backup-release-and-emergency
OWNER: ChatGPT reestruturacao
DATE: 2026-11-06
BASE_MAIN_SHA: 1eaac92a5a8b6c6a50cbd6e2fd8daa84e5fd8e63
SUPERSEDES: 20261106-opt07-08-ara-release-protection-ready.md
TARGETS: .github/workflows/cloudflare-ara-backup-deploy.yml; .github/workflows/trigger-cloudflare-ara-backup-deploy.yml
BASELINE_PROVEN: PR #2137 governa o deploy stateless por SHA; a rota stateful manual ainda aceita disparo sem SHA e pode substituir o mesmo Cloudflare Worker.
FAILED_AVOIDED: nenhuma chamada a deploy, secret, PC executor ou novo recurso.
SUCCESS_SIGNAL: os dois workflows exigem SHA exato, incidente e reconhecimento explicito antes de tocar o Worker stateful.
FAILURE_SIGNAL: SHA divergente, incidente ausente, branch diferente de main, concorrencia.
TEST_VALIDITY: verificacao estatica dirigida, sem job executado.
COST_ADDED: R$0
ROLLBACK: PR revert normal.
