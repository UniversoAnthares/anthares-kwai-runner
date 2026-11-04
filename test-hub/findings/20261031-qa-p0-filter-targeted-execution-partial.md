# QA P0 PR #2015 — testes dirigidos executados fora do PC, integração externa pendente
STATUS: PARTIAL
AREA: architecture/qa-p0-incident-remediation
DATE: 2026-10-31 UTC
RUN: local-isolated-sandbox (no GitHub Actions run)
JOB: none
COMMIT: 933327b5d28c5b16848860b5fd9492ba41237b80
SUPERSEDES: 20261031-qa-p0-nonpublisher-false-alerts-running.md
OWNER: Reestruturação e Otimização / 00 — Auditoria e decisões
TEST_VALIDITY: Foram extraídos o corpo exato da função workflow_incidents do blob GitHub 3c0f0e146eb02787d415155bddf968a0d04f093d e o filtro regex da workflow do blob fe5bd583a37e0d6545d60ca50124c9c41b508c35. Funções auxiliares/ambiente simulados sem rede, nenhuma execução do projeto completo. Arquivos temporários da sessão em /mnt/data/anthares-qa-validation (não no PC do titular).
BASELINE_PROVEN: main 7a44b8c64f83fd4498d81c18d3d773424a844467; GH e GitLab blobs idênticos antes da proposta. GitHub repo última execução visível 2026-10-30T21:13:53Z, repo AVS executou após essa data em 2026-10-31T03:53Z.
OFFLINE_PYTHON: python 3.13.5; 8 unittest passed in 0.004s. Casos: 5 origens não publicadoras excluídas; três publicadores reais preservados; sucesso sem alerta; fila <20min ignorada; fila >=20min alerta; falha antiga >2h ignorada; mesmo nome/dia deduplicado; erro HTTP403 no repo secundário mantém alerta parcial. Uma função do PR foi executada; os testes completos do repositório NÃO foram executados.
OFFLINE_JAVASCRIPT: Node.js v22.16.0; 9/9 node:test passed (TAP 1..9). Cinco exclusões e quatro publicadores reais preservados com a regex literal do PR. NÃO é execução de GitHub Actions.
ACTUAL_CODE_VALIDATION: Classificadores funcionaram nas hipóteses dirigidas; confiabilidade de integração/autenticação/schedule em produção ainda UNVERIFIED.
GITHUB_ACTIONS: Não há workflow_runs e check statuses registrados para o commit PR #2015. Causa de suspensão/ausência de agendamento ainda NÃO COMPROVADA. Incidente geral do GitHub Actions em 2026-10-30 17:50–19:23 UTC está resolvido; o último run local observado é 21:13 UTC, portanto não atribuir a parada automaticamente ao incidente. GH tool disponível lê Actions/runs, mas não expõe endpoint de ativação ou dispatch de workflow; GitLab CI GET 403; Browserless Free 0/1000 units; Vercel/other quota constrained. No cross-service bypass after security denial.
SUCCESS_SIGNAL: CI da PR com unit suite real e execução hospedada real após correção de permissão/quota; então readback de ausência de novos falsos P0, publicadores permanecem ativos, ledger de publicações intocado.
FAILURE_SIGNAL: filtro elimina publicador real; novas issues espúrias de diagnóstico; CI continua sem gerar runs; GitHub billing restriction ou workflow disabled que só admin/support pode sanar.
NEXT_ACTION: verificar e recuperar GitHub Actions em Settings > Actions > General e workflow status com titular autorizado, sem alterar políticas financeiras; somente após prova pública nova de run reavaliar promoção do patch.
COST: 0 serviços/créditos novos, 0 publicações, 0 workflows redisparados e 0 arquivos no computador pessoal.
ROLLBACK: revert PR #2015 caso regressão após merge, respeitar head/lease de produção.
AOI: item fixo 16 permanece PARTIAL.
