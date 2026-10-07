# anthares-control Git provider failover
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-07
RUN: https://anthares-control.anthares1.workers.dev/git-provider-self-test
JOB: Cloudflare Version 2c523abc-d839-45aa-b7c8-1a0735f6a1f5
COMMIT: f148f645628b441a633eb51a8bb81b5256c917a2
SUPERSEDES: none

## Objetivo
Integrar a politica GitHub/GitLab ao anthares-control e provar os cinco cenarios fail-closed solicitados.

## Resultado
PROVEN no modulo deterministico e no Worker implantado. GitHub disponivel seleciona GitHub; GitHub BLOCKED_QUOTA/DOWN permite failover para GitLab somente com checkpoint igual; GitLab DOWN permite retorno ao GitHub com checkpoint igual; ambos indisponiveis bloqueiam; SHA divergente bloqueia.

## Evidencia decisiva
Self-test local retornou ok=true. Deploy Cloudflare concluido, Version ID 2c523abc-d839-45aa-b7c8-1a0735f6a1f5. Endpoint publico /git-provider-self-test retornou ok=true com github->gitlab, gitlab->github, both_unavailable blocked e checkpoint_diverged blocked.

## Consequencia
anthares-control agora contem a politica de decisao/failover. Endpoints de decisao/failover reais exigem adminAuth. Nenhuma credencial de provedor foi colocada no codigo. Proximo passo da camada de mirror e fornecer transporte de escrita autenticado fora do GitHub Actions; GITLAB_MIRROR_URL continua segredo e nao deve ser commitado.
