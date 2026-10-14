# Lease renewal — deploy CORTES WordPress
STATUS: PROVEN
AREA: wordpress-deploy
DATE: 2026-10-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38497893438
JOB: deploy
COMMIT: 2761fda6c894fb4e0aa83baf1a5e4e1b98d85ca5
SUPERSEDES: test-hub/findings/20261014-0014-lease-wordpress-cortes-deploy.md
OWNER: chatgpt-cortes-finalization
LEASE_START_UTC: 2026-10-14T00:41:00Z
LEASE_EXPIRES_UTC: 2026-10-14T01:51:07Z

## Objetivo
Concluir publicação e validação do plugin CORTES no WordPress real e restaurar os harnesses temporários.

## BASELINE_PROVEN
O código-fonte aplicado veio exatamente do commit GitHub `2761fda6c894fb4e0aa83baf1a5e4e1b98d85ca5` de `UniversoAnthares/anthares-wordpress`.

## RESULT
O deploy final usou GitHub Actions público apenas como executor efêmero, recuperando credenciais de implantação em runtime pelo secret bridge GitLab já existente, sem expor valores. O job alcançou o Hostinger real, executou PHP lint no plugin, fez backup do plugin anterior, troca atômica, ativação, migração CORTES e validação via WP-CLI.

Evidência emitida pelo Hostinger real:
- `CORTES_LIVE_DEPLOY=PROVEN`
- plugin `2.7.3`
- função `anthares_cortes_render=true`
- página `CORTES`, ID `16680`, slug `cortes`, status `publish`
- schema `2`
- rotas `/anthares/v1/cortes/state` e `/anthares/v1/cortes/network` registradas
- `legacy_cutoff=137`
- `short_max=100`
- YouTube ativo para `long`
- Kwai ativo para `short`
- TikTok, Instagram, Facebook, Threads, X, Pinterest e LinkedIn cadastrados e desativados
- `CORTES_CONTROL_SHA=64a67c5e0abbd9dacff6c70b62690853d89e41468b8eff16f6075cfacac29225`
- `CORTES_MIGRATIONS_SHA=78c81deecde139de6476872b188db06b487c3db01fbcdb9d38a7dc2cba41aa1b`
- smoke público `https://anthares.us/cortes/` retornou HTTP 200.

O workflow one-shot foi removido após o sucesso. O `.gitlab-ci.yml` principal havia sido restaurado ao conteúdo original antes desta validação e permanece fora do caminho de deploy final.

## FAILED_AVOIDED
Render não foi usado como dependência de produção porque sua cota gratuita está esgotada. PC/ARA offline não foi necessário. GitLab shared runner com quota insuficiente não foi usado no deploy final.

## SUCCESS_SIGNAL
Atendido: Hostinger real carregou o build esperado, passou lint, WP-CLI validou CORTES e o endpoint público da página respondeu 200.

## TEST_VALIDITY
Validação executada no Hostinger real carregando a instalação `anthares.us`. Nenhuma publicação social foi executada.
