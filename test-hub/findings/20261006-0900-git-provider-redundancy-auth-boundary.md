# Git provider redundancy — prepared, external authorization required
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37465604828
JOB: mirror-gitlab 112275714669; mirror-codeberg 112275715047; verify 112275795759
COMMIT: 33142c4e4178837dec416540a2ab38140393a875
SUPERSEDES: none

## Objetivo
Preparar redundância GitHub → GitLab e GitHub → Codeberg independente, com CI/failover/check de SHA, e avançar o acesso de agentes até a fronteira real de autorização.

## Resultado
PROVEN: camada fail-closed criada em tools/git-provider-sync.sh, tools/cross-provider-sha-check.py, docs/GIT_PROVIDER_FAILOVER.md e .github/workflows/git-provider-redundancy.yml.
PROVEN: checker retorna all_equal=true quando três endpoints expõem o mesmo SHA.
PROVEN: checker retorna AUTH_REQUIRED e exit 2 quando GitLab/Codeberg não estão configurados.
PROVEN: workflow real 37465604828 executou os dois mirrors independentemente e verify; ambos recusaram operar sem target configurado, sem expor secrets.
PROVEN: GitLab MCP oficial existe no Free tier e Codex local foi configurado com https://gitlab.com/api/v4/mcp; OAuth foi iniciado e aguarda autorização humana.
PARTIAL: GitLab repository mirror e CI real aguardam conta/OAuth/credencial do destino.
PARTIAL: Codeberg repository mirror e Forgejo MCP aguardam conta/token do destino.

## Evidência decisiva
GitLab mirror: TARGET_NOT_CONFIGURED provider=gitlab, exit 78.
Codeberg mirror: TARGET_NOT_CONFIGURED provider=codeberg, exit 78.
Verify: GitHub UP no SHA 33142c4e4178837dec416540a2ab38140393a875; GitLab/Codeberg AUTH_REQUIRED; exit 2.
Teste local sintético com três URLs GitHub idênticas: all_equal=true para o mesmo SHA.
GitLab MCP foi gravado em ~/.codex/config.toml e o fluxo codex mcp login GitLab foi iniciado.

## Consequência
Não marcar GITLAB_REPOSITORY_REDUNDANCY, GITLAB_CHATGPT_ACCESS, CODEBERG_REPOSITORY_REDUNDANCY, CODEBERG_CHATGPT_ACCESS ou CROSS_PROVIDER_SHA_CHECK como PROVEN até haver provedores reais. Após autorização, criar/importar destinos, cadastrar secrets e executar o workflow até mirror+verify verdes; depois testar escrita/branch/CI/MCP e desastre. Nenhum merge/force-push automático diante de divergência.

## Lease closure
O lease 20261006-0858-lease-architecture-git-provider-redundancy.md fica encerrado nesta fronteira de autorização externa.
