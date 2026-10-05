# Profile probe exposed server/resource gate
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: 111992783329
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: none

## Objetivo
Partir do adaptive comprovado e testar a navegação para Profile/login.

## Resultado
O job profile-text concluiu o harness, mas não expôs login. A UI final mostrou simultaneamente a navegação Home/Discover/Inbox/Profile, "Can't connect to server" e "Resource downloading ... 5%". Portanto o próximo gargalo observável é conectividade/download de recursos antes de interpretar Profile como falha de navegação.

## Evidência decisiva
Log: PROFILE_UI=can’t connect to server ... home discover inbox profile ... resource downloading you'll have access to all the features when it’s done.
O Kwai instalou e lançou normalmente antes disso: KWAI_LAUNCHED.

## Consequência
Não repetir profile-text isoladamente como tentativa de login. Separar e testar primeiro conectividade/backend e conclusão do resource download; depois repetir somente a melhor rota de Profile. O harness verde significa execução do probe, não autenticação comprovada.
