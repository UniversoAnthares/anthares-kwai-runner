# Produção Cloudflare está comprovadamente atrás do snapshot e ainda seleciona PC
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389095100
JOB: 112029634704
COMMIT: c8dece95d78f62b551f9254e56d3c682b4f06214
SUPERSEDES: none

## Objetivo
Comparar o Worker realmente ativo com o snapshot endurecido sem mutar produção.

## Resultado
O Worker ativo responde e tem estado persistente, mas está desatualizado. /strategy ainda anuncia local como fallback para cuts, TikTok, Kwai, Kwai LIVE e control; /failover-self-test ainda termina em local. Portanto produção viola a arquitetura PC-off apesar de o snapshot novo estar correto.

## Evidência decisiva
Run 37389095100: /health ok/persistent_state=true; /strategy retornou cuts render->github->local, tiktok render->github->local, kwai kwai_web->local, kwai_live hls_origin->local e control cloudflare->github->render->local. /failover-self-test retornou after_github_failure=local.

## Consequência
Até o deploy do snapshot novo, nenhum chamador deve confiar em seleção local retornada pelo Worker; consumidores devem aceitar somente executores explicitamente permitidos. Deploy continua bloqueado pela ausência de CLOUDFLARE_API_TOKEN no runner público.
