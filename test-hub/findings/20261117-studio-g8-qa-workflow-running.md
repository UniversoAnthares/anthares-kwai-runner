# Studio G8 — contrato de QA isolado no workflow manual existente

STATUS: RUNNING
AREA: anthares-studio/g8/manual-qa-contract
DATE: 2026-11-17
OWNER: ChatGPT / OBSERVATORIO IPB
JOB: studio-g8-qa-manual-20261117
SOURCE: UniversoAnthares/anthares-wordpress PR #317 head 81484ac4e0a284f8a3d45afca19abca595251b70
PEER: GitLab feat/studio-g5-private-cpt-admin-20261117 ausente 404.
BASELINE_PROVEN: workflow anthares-qa.yml existente usa workflow_dispatch sem gatilho cron/PR e tem job QA Ubuntu/PHP8.5. Head da PR #317 adicionou teste PHP para CPTs.
FAILED_AVOIDED: não disparar workflow/runner com quota incerta; não criar workflow novo nem tocar produção.
SCOPE: uma etapa estática do novo plugin no workflow manual existente .github/workflows/anthares-qa.yml, exclusivamente branch feat/studio-g5-private-cpt-admin-20261117. Executar Python unittest e PHP lint, sem leitura de segredos/Hostinger.
SUCCESS_SIGNAL: etapa explícita e executável em workflow manual; lint sintático do YAML e PHP, manifesto 665/665 sem caminhos novos.
FAILURE_SIGNAL: alteração de triggers/segredos, falta de cobertura, conflitos com jobs existentes.
TEST_VALIDITY: preparação de CI; sucesso de execução hospedada ficará pendente até dispatch autorizado sem aumento de custo.
ROLLBACK: reverter só o commit da etapa no PR draft #317.
