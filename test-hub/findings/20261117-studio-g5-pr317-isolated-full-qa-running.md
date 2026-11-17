# Studio PR317: QA integral isolada em Hostinger

STATUS: RUNNING
DATE: 2026-11-17
AREA: anthares-studio/g5/qa-isolated-pr317
JOB: studio-pr317-hostinger-full-qa-20261117
OWNER: ChatGPT / OBSERVATORIO IPB
SOURCE: UniversoAnthares/anthares-wordpress PR #317 HEAD ef6db8c94395bbbc448925fc66887c04f9f59060
PEER: GitLab branch feat/studio-g5-private-cpt-admin-20261117 absent (404).
BASELINE_PROVEN: remote Hostinger authorized, existing isolated QA clone can reach GitHub via its stored origin; upstream branch HEAD verified by git ls-remote. PHP8.3, Python3, repository QA tools present.
FAILED_AVOIDED: nenhuma gravação de WordPress/REST em produção, nenhuma leitura autenticada de aba de navegador negada.
SCOPE: clone TEMPORÁRIO, independente de checkouts de outros agentes, dentro de anthares-private-storage (Hostinger) e remoção obrigatória em EXIT. Executar todos os testes unittest do plugin, PHP 8.3 lint de seus arquivos, manifesto exactly-once e orquestrador de QA. Evitar chamar WordPress, WP-CLI, dados reais ou API de publicação.
SUCCESS_SIGNAL: Python unittest todos PASS, quatro PHP lint PASS, manifesto 665/665 PASS e QA orquestrador PASS.
FAILURE_SIGNAL: falha registrada fielmente, sem tocar em produção; clone removido mesmo com erro.
TEST_VALIDITY: garante código em HEAD isolado; cobertura do fluxo REST real de escrita e UI autenticada continua fora deste teste.
ROLLBACK: nenhuma alteração produtiva, cleanup do clone temporário.
