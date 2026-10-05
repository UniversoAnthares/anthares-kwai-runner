# Login inspector false green; parallel parent-route probes started
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381245242 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381259065
JOB: 8-route matrix + fixed inspector
COMMIT: 5104be288894bfe9f545a42b0201051f10f34924
SUPERSEDES: test-hub/findings/20261005-2235-login-ui-inspector-running.md

## Objetivo
Corrigir o falso verde do inspector e testar em paralelo rotas causais baseadas no controle Profile real.

## Resultado
O run 37380670886 terminou verde, mas o hub provou que ficou preso no permissioncontroller; portanto não testou login. O inspector já limpa esse diálogo e agora clica especificamente o pai clicável com.kwai.video:id/ll_profile. Além disso, foi disparada matriz paralela com oito variantes: parent-now, parent-wait10, parent-wait30, parent-restart, parent-twice, parent-back-parent, parent-scroll e parent-resource-wait.

## Evidência decisiva
Finding anterior 20261005-1820 mostra permission_allow/deny em todos snapshots do run verde. Finding 20261005-2220 prova ll_profile clickable=true e que clicar no TextView não bastava.

## Consequência
Não considerar 37380670886 prova funcional. Usar 37381259065 para árvore UI corrigida e 37381245242 para escolher em paralelo a rota que produza AUTH_CANDIDATES/form/editable ou mudança inequívoca de Profile.
