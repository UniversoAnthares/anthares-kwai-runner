# Matriz corrigida de onboarding executou 10 estratégias
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37377433515
JOB: matrix with 10 acceptance jobs
COMMIT: bdda1fe034d98e3dc0869c98958995b6ca8cd381
SUPERSEDES: none

## Objetivo
Substituir a matriz anterior cujo harness quebrava heredoc Python e testar estratégias reais de navegação do Kwai com um script versionado.

## Resultado
Os dez jobs — baseline, swipe, activity, intent, inspect, adaptive, tap, permission, back e settings — concluíram success. Android inicializou, o vault instalou o Kwai e o probe versionado executou em cada estratégia. Isso prova que a matriz corrigida realmente executou os probes; não prova, isoladamente, sessão autenticada.

## Evidência decisiva
Todos os jobs do run 37377433515 terminaram success. Nos logs há KWAI_LAUNCHED seguido por execução de python3 kwai_onboarding_probe.py e MODE=<estratégia>, com artefatos por estratégia. Exemplo baseline: KWAI_LAUNCHED, depois MODE=baseline.

## Consequência
Não repetir a matriz quebrada do run 37372686273. Usar o script versionado como harness. Não interpretar o verde dos probes como autologin PROVEN sem evidência de estado autenticado. A próxima camada válida é descobrir uma rota determinística para perfil/login e então executar autologin/auth probe real.
