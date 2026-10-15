# Provider quota and regression baseline
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-15
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38674949469
JOB: 116226316086
COMMIT: 8dd0a1baf3705a06fdd3a4971208e7eabebd1a16
SUPERSEDES: none

## Objetivo
Fixar a regra operacional solicitada: somente Anthares Remote para controle remoto, somente Anthares Browser para navegador, aposentar permanentemente Render/TinyFish/CircleCI/Browserless, separar falha de componente Anthares de quota externa e exigir rechecagem de regressão por rodada.

## Resultado
- Anthares Remote foi verificado com heartbeat recente e chamadas `remote_exec` reais bem-sucedidas.
- GitLab CI foi confirmado como `BLOCKED_QUOTA`: pipeline 2947796926, 25 jobs, `failure_reason=ci_quota_exceeded`, nenhum runner alocado.
- GitHub Actions público segue capaz de alocar hosted runner; o watchdog anterior falhou por lógica/configuração local, não por quota.
- Cloudflare control e x-vault responderam HTTP 200; `anthares-control` reportou `persistent_state=true`, `queue_bound=true`, `pc_fallback=false` e routing revision sem Render.
- `anthares-reserva-browser` respondeu HTTP 200 com browser/durable-state bindings ativos; sessão autenticada continua separada e não foi inferida.
- Northflank `anthares-ara-northflank` e `anthares-tiktok-northflank` estão BUILD=SUCCESS e DEPLOY=COMPLETED. Saldo de quota Northflank não foi inferido.
- GitHub Actions privado permanece bloqueado por quota segundo informação do proprietário; o conector disponível não expõe billing account-level, portanto a confirmação direta de saldo permanece pendente.
- Cloudflare Browser Rendering permanece inelegível pelo último 429 conhecido; esse estado não contamina Workers runtime/Durable Objects. Workers Builds passa a exigir prova fresca antes de seleção.
- Render, TinyFish, CircleCI e Browserless permanecem ineligíveis por política; Browserless foi substituído por Anthares Browser.

## Regressão encontrada e corrigida
Run 38674709184 do `Anthares Resilience Watchdog` falhou porque o workflow tentava provar runtime usando URLs/flags externas vazias. Isso era um falso positivo de regressão: o próprio GitHub-hosted runner não possui evidência de heartbeat do Anthares Remote nem URL canônica de `/ready` do Anthares Browser.

Correção:
- `tools/anthares_resilience.py` ganhou modo `ANTHARES_RESILIENCE_REPORT_ONLY=1`, que nunca fabrica saúde; apenas não converte ausência de evidência externa em falha de policy CI.
- `.github/workflows/anthares-resilience-watchdog.yml` agora valida invariantes de roteamento diretamente, usa a variável correta para browser primary e reporta separadamente a evidência runtime disponível.
- Run sucessor 38674949469: policy guard, compile e runtime-report steps passaram; job estava concluindo cleanup quando registrado.

## Fonte de verdade criada
- `ci-hub/provider-status.json`: estado machine-readable, classe de evidência, elegibilidade, quota e condição de reabertura.
- `ci-hub/CONTINUITY.md`: árvore de decisão e protocolo obrigatório de regressão por rodada.
- `ci-hub/executor-routing.json` r13: roteamento alinhado ao estado verificado e sem defaults aposentados.

## Consequência
Próximos agentes NÃO devem:
- usar qualquer remote diferente de Anthares Remote;
- usar Browserless/TinyFish como browser fallback;
- usar Render ou CircleCI;
- selecionar GitLab CI enquanto `ci_quota_exceeded` persistir;
- selecionar GitHub Actions privado sem prova fresca de renovação;
- interpretar Cloudflare Browser Rendering 429 como indisponibilidade geral do Cloudflare.

Próximos agentes DEVEM iniciar cada rodada com regressão read-only, atualizar `provider-status.json` quando a evidência mudar e reparar componente Anthares antes de migrar sua função. Migração só é a resposta automática quando a causa for quota/outage de infraestrutura externa ou dependência de provedor aposentado.
