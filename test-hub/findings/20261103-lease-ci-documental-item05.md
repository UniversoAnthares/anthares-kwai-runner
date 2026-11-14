# Lease — item 05: gatilhos documentais em WordPress
STATUS: RUNNING
AREA: wordpress-ci-triggers
DATE: 2026-11-03T15:33:47.812Z
OWNER: ChatGPT / projeto Reestruturação e Otimização / item 05
EXPIRES_UTC: 2026-11-03T15:58:47.812Z
REPOSITORY: UniversoAnthares/anthares-wordpress
SCOPE: .github/workflows/anthares-qa-source-sync.yml e mirror-redundancy.yml, apenas filtros de trigger em push. Sem alteração em deploy, cron, runner, credenciais ou publicador.
BASELINE_PROVEN: GitHub main em modificação concorrente de anthares-home; source-sync blob 815972c9b80e0b5013295c16e2e68a776ed9e538; mirror-redundancy blob bf492313224c3f1297ec7838e457da17bc6f45c3; GitLab main SHA distinto, não reconciliar nesta alteração.
FAILED_AVOIDED: disparo de QA/mirror por alterações exclusivas em docs/ e test-hub/.
SUCCESS_SIGNAL: diff limitado aos filtros; mudança funcional ainda elegível; manifesto QA do PR preservado; aprovação PR antes do merge.
FAILURE_SIGNAL: perda de gatilho em PHP/JS/CSS/YAML; alteração de execução ou de schedule; base concorrente.
TEST_VALIDITY: branch de lease exclusiva; confirmar SHA antes de editar branch de trabalho; máximo 25 minutos.
SUPERSEDES: none
