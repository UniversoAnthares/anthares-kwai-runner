# Autorização GitHub Actions para criação automática de PR — teste isolado
STATUS: RUNNING
AREA: ai-remote-claude-router/pr-permission
DATE: 2026-10-19
LEASE_OWNER: ChatGPT/github-actions-pr-permission-check
BASE_HEAD: 81eff9159a7acbd78fe7d29628593052a9658b36
EXPIRES_UTC: 2026-10-19T23:50:00Z
BASELINE_PROVEN: test-hub/findings/20261019-2250-free-claude-code-remote-real-proven.md, Claude Code plan/edit/fallback PROVEN, PR #209 aberto por conector, run 39337326780.
FAILED_AVOIDED: GitHub Actions gh pr create anteriormente bloqueado por política do repositório; usuário informou agora que habilitou Allow GitHub Actions to create and approve pull requests.
SUCCESS_SIGNAL: workflow GitHub Actions independente cria branch claude-free/pr-permission-proof-* com um arquivo de teste e PR rascunho automaticamente; log ANTHARES_FREE_AUTO_PR=PASS; PR verificado via API e diff estrito.
FAILURE_SIGNAL: 403/GraphQL política ainda restritiva, token sem permissões, push não confirmado, tentativa de mudança fora de escopo, ou PR não criado.
TEST_VALIDITY: workflow concluído sem PR e sem sinal decisivo não conta como sucesso. Não usar inferência/IA nem planos pagos, não escrever em main no job.
SCOPE: Novo workflow de teste GitHub somente; documentação Test Hub; não modificar CORTES, AI Hub, secrets, Bitwarden, Anthares Remote ou configuração administrativa.
PEER_CHECK: GitLab main .github/workflows consultado; caminho anthares-free-claude-pr-permission.yml ausente.
