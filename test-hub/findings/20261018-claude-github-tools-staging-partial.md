# Claude Free GitHub MCP: safe staging implementation
STATUS: PARTIAL
AREA: claude-github-tools
DATE: 2026-10-18
RUN: none
JOB: Anthares Remote c2396fbe970b3b5bb423e13ee4f4aec7 (Node QA); 8a71f62c2aed2beaff846626eaf02708 (Wrangler dry-run)
COMMIT: c4133032b21415b88ad3534cc9592d6b860019bc
SUPERSEDES: 20261018-claude-github-tools-lease.md

## Resultado
Draft PR #162 em https://github.com/UniversoAnthares/anthares-kwai-runner/pull/162. Branch integration/claude-free-mcp-20261018; main permanece sem o código do Claude. O gateway incorpora cliente publicado e comprovado Claude.ai OAuth CIMD, callback exato e scopes ara.read/github.read/github.write; nega ara.write ao Claude. Cinco ferramentas GitHub permitem consulta, lease, branch claude/*, put com HEAD/blob SHA e draft PR, respeitando lista fixa de cinco repositórios. Token de escrita reside exclusivamente no secret ANTHARES_GITHUB_TOKEN quando configurado.

## Evidência decisiva
- GET Claude CIMD 200 em 2026-10-18, client_id https://claude.ai/oauth/mcp-oauth-client-metadata; callback https://claude.ai/api/mcp/auth_callback.
- GET Anthares MCP /health 200, backend conectado; OAuth AS metadata 200.
- Testes Node --check 5/5 OK; node --test 11/11 PASS, 0 FAIL, Node 24.19.0, Anthares Remote job c2396fbe970b3b5bb423e13ee4f4aec7. Testes feitos com clone de arquivos SHA-pinned e pasta temporária descartada.
- Wrangler 4.149 deploy --dry-run EXIT 0 e bundle gerado; Anthares Remote job 8a71f62c2aed2beaff846626eaf02708. Não executou deploy.
- Código antigo de OAuth ChatGPT preservado em branch. GitHub main/GitLab main do código base da fonte index.js tinham blob SHA 273d1af68ee486ee0291d6c1fa0f025a270020f9.
- Git tree usado na consulta de leases para evitar limite GitHub de 1.000 itens em Contents API.
- Wrangler autenticado, mas tentativa de listagem de secrets falhou sem prova de que o token GitHub está configurado.

## Pendências
1. Provisionar token GitHub fine-grained de escopo mínimo no segredo Cloudflare ANTHARES_GITHUB_TOKEN (não divulgar em chat, issues ou repositórios).
2. Revisar OAuth completo contra produção (PKCE, OTP, refresh, replay, metadados, escopos) sem modificar autenticação do ChatGPT; implantar com reversão segura após testes.
3. Autorizar conector personalizado MCP na conta Claude gratuita; testar leitura e edição via Claude em arquivo descartável e draft PR.
4. Verificar funcionamento do serviço Anthares Browser como integração separada somente após base MCP confirmada.

## Consequência
STAGED/PARTIAL. Não anunciar conexão funcional, GitHub write em produção ou integração com Anthares Browser. Não usar GitHub Actions para esse teste, não alterar CORTES, não reiniciar/desligar/logoff do Windows, não mesclar PR #162 sem checklist de credenciais e OAuth.
