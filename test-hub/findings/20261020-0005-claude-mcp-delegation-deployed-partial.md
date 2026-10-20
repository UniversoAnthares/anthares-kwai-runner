# Claude Free via MCP Anthares → Claude Code GitHub remoto
STATUS: PARTIAL
AREA: claude-mcp-code-delegation
DATE: 2026-10-20
LEASE_STATE: CLOSED
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39345333579
COMMIT: 38d391e725e722ccc85a5fc0ab99f217c7f00230
SUPERSEDES: test-hub/findings/20261019-2351-lease-claude-code-delegation.md

## Objetivo
Usuário autorizou integração direta do Claude Free da interface Anthropic ao executor Claude Code/9Router/Gemini no GitHub Actions, sem VPS, planos pagos ou PC.

## Resultado
- CI contrato: GitHub Actions run 39345229461, todos os testes da ponte e build real Wrangler dry-run PASS.
- Fonte GitHub: PR #214 merged, commit 38d391e725e722ccc85a5fc0ab99f217c7f00230. GitLab peer `cloudflare-ara-mcp/src/github-bridge.mjs` blob 2508e45d196c65c22d2b5901fafd1b6805b5794f verificado equivalente após merge.
- Implante Cloudflare: run 39345333579, job 118376438848; ANTHARES_CLAUDE_BRIDGE_REVIEWED_TESTS=PASS; ANTHARES_CLAUDE_MCP_SECRETS_PRESENT=PASS; ANTHARES_PREDEPLOY_OAUTH_HEALTH=PASS; ANTHARES_CLAUDE_BRIDGE_DEPLOYED=PASS; ANTHARES_CLAUDE_BRIDGE_ANON_MCP_DENIED=PASS; ANTHARES_CLAUDE_BRIDGE_DEPLOY_ACCEPTANCE=PASS.
- Worker implantado: dc6408ba-02fa-4ab5-a439-1760d3ec571e. OAuth GitHub proprietário, MCP, Vercel/ARA control_ready, anonymous 401 preservados.
- Capacidades adicionadas a MCP autenticado: run_claude_code (github.write); get_claude_code_status, get_claude_code_result (github.read). Reusa OAuth atual, GitHub secret server-side, request UUID interno, validação de escopo, sem edição de main e com draft PR. Workflow existente recebe request_id e faz resultado ZIP STORE temporário.
- CI testou caminhos proibidos, proteção contra adulteração de request ID, origem de redirect do artifact, proibição de repassar token GitHub, limites de tamanho e comportamento em erro.
- Execução GitHub Claude Code em isolamento com modelos gratuitos estava PROVEN previamente no Test Hub (run 39336129062 plano, 39337326780 edição e fallback, 39339550110 draft PR pelo workflow).

## Evidência pendente
- A sessão Claude Free do proprietário ainda precisa invocar efetivamente run_claude_code, depois get_claude_code_status e get_claude_code_result e comprovar que ANTHARES_GITHUB_TOKEN do Worker tem permissão Actions:write/read de workflow/artifacts. Essa sessão/autorização está fora da ferramenta GitHub Actions e não se deve falsificar OAuth. CI e implantação PROVEN; end-to-end Claude Free caller→result NOT_TESTED.
- Se GitHub retornar 403 à execução, identificar falta de permissões do fine-grained token de Actions e atualizar pelo fluxo secreto autorizado, nunca expor/rotacionar credencial às cegas. Se Claude não mostrar novas ferramentas, reabrir conversa ou atualizar conector autorizado, sem refazer login desnecessariamente.
- O workflow segue sujeito a limites gratuitos Gemini/GitHub. Os resultados são pessoais à conta autorizada; o artifact expira após 2 dias.

## Consequência
Não repetir deploy ou alterar OAuth sem causalidade concreta. Não classificar user-to-Claude-MCP flow PROVEN até execução autenticada real. CORTES, WordPress, Cloudflare secrets, PC e funções legadas preservados.
