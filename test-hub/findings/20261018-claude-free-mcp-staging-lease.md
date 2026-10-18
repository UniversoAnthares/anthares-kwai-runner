# Integração Claude Free com Anthares MCP: estágio isolado
STATUS: RUNNING
AREA: claude-mcp-staging
DATE: 2026-10-18
START_UTC: 2026-10-18T14:06:12.324Z
EXPIRES: 2026-10-18T14:31:12.324Z
LEASE_OWNER: ChatGPT/Claude-free-onboarding
BASELINE_PROVEN: GitHub runner ec3528e4f77b537431fca5a12611fbddb2d8b388; Claude Free permite um MCP remoto personalizado; MCP Cloudflare atual permite OAuth com PKCE somente para chatgpt.com, com pinnedClient; GitLab main 2fdb3e0c958e9e105112c3dc90a999742f3c48ff; Anthares Remote read-only status connected.
FAILED_AVOIDED: não iniciar Claude Code pago, não depender de GitHub Actions/cotas, não usar automação de navegador para autenticação, não modificar tokens ou sessões e não substituir cliente ChatGPT pinado.
SCOPE: apenas branch isolada com compatibilidade OAuth Claude Free, testes estáticos e instruções seguras; sem deploy, sem mutação da fila de publicação, sem reinicialização ou operação local.
SUCCESS_SIGNAL: draft PR GitHub com diff mínimo, testes de allowlist/PKCE/segregação do client, GitLab peer comparado, sem merge ou implantação.
FAILURE_SIGNAL: invasão de client pinning do ChatGPT, domínio de redirect permissivo, acesso de escrita indevido, regressão sintática.
TEST_VALIDITY: confirmar HEAD/blob/peer imediatamente antes de cada write, verificar testes explicitamente; resultado de CI sem logs não equivale a PROVEN.
SUPERSEDES: none

## Observação
Lease independente das áreas CORTES/Kwai/WordPress e do controle operacional, sem ativação de execução real. A expiração deste lease ocorre em até 30 minutos.
