# Anthares Claude Free MCP: changes staged for review
STATUS: PARTIAL
AREA: claude-mcp-staging
DATE: 2026-10-18
RUN: none
JOB: none
COMMIT: c37eff91b8b0f33d78002294c67b8ec6bcc8148f
SUPERSEDES: 20261018-claude-free-mcp-staging-lease.md

## Objetivo
Começar integração sem assinatura Claude Pro, preservando Anthares em produção.

## Resultado
Branch `integration/claude-free-mcp-20261018` e draft PR #162:
https://github.com/UniversoAnthares/anthares-kwai-runner/pull/162
Compatibilidade OAuth para client ID Claude publicado e callback exato; scopes read-only e listagem MCP de ferramentas filtrada. Guia de integração e regras CLAUDE.md adicionados. Sem deploy, sem alteração em GitLab, sem alteração no Anthares Remote físico, sem credenciais novas.

## Evidência decisiva
- 16 validações da política OAuth executadas no ambiente JS, 16 aprovadas.
- 12 validações integradas de funções OAuth com mocks, 12 aprovadas.
- Verificação final V8 de sintaxe e funções do gateway: 11/11 aprovada.
- SHA-base index.js GitHub e GitLab coincidia: 273d1af68ee486ee0291d6c1fa0f025a270020f9.
- Não houve teste OAuth real nem execução do arquivo Node `claude-client-policy.test.mjs`; execução CI suspensa pela política de cotas.

## Próximas ações
Validar metadata de cliente publicada, OAuth real, OTP, PKCE, refresh, token replay e isolamento; depois implementar MCP GitHub branch+PR com segredo servidor e escopos restritos. Somente após revisão implantar. Claude Free possui limite de 1 conector personalizado. Ninguém deve confundir este estágio com integração concluída.
