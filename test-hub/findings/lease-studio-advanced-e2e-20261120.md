# Lease — homologação avançada Anthares Studio
OWNER: ChatGPT / STUDIO_ADVANCED_E2E_20261120
STATUS: CLOSED_QA_PASS_DEPLOY_PENDING
START_UTC: 2026-11-20T01:40:00Z
EXPIRES_UTC: 2026-11-20T02:30:00Z
SITE: https://anthares.us/studio/ ; somente projeto temporário QA-AVANCADO-STUDIO-20261120 e seus filhos rastreados.
BROWSER: Chrome perfil AntharesStudioAuth, CDP localhost:9241, aba agente criada e fechada ao concluir. Preservar aba interativa do usuário.
GITHUB_REF: UniversoAnthares/anthares-wordpress main 075e525780064340f28eceb59b128ef4de5f13c8.
APPROVED: clicar e validar funcionalidades avançadas de uso privado, versões, exportação e importação em artefatos de teste reversíveis; checar responsividade e respostas REST. Nenhuma publicação pública, envio de mensagens, pagamentos, ações externas nem exclusão de registros existentes.
SAFEGUARDS: previa conferência de autoria, IDs e metadados; QA fixture com nome exclusivo; rollback/remoção dos próprios registros; conservar código legado; correção de código só após preflight CAS, backup, testes e sem bloqueio de segurança.
ACCEPTANCE: evidências por controle, resultados PASS/FAIL/SKIP, exceções e fechamento dos recursos de QA.

CLOSED_UTC: 2026-11-20T02:29:00Z
EVIDENCE: test-hub/findings/20261120-studio-advanced-e2e-fix-report.md. 12 QA posts removed and database verified zero, 22 original projects unchanged, QA browser tab closed. GitHub PR #384 prepared; manual FTP install and post-deploy QA pending; no unauthorized deployment.
