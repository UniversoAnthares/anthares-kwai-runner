# Stabilization evidence favors restart-after-nav
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378856592
JOB: 111995195964
COMMIT: fd5ef6b7f82431b43cb8e43d287dc9dc6ce8e837
SUPERSEDES: none

## Objetivo
Identificar uma alteração causal que estabilize o estado pós-onboarding.

## Resultado
Entre os jobs já concluídos, restart-after-nav produziu feed real + Home/Discover/Inbox/Profile sem a mensagem Can't connect e sem Resource downloading no FINAL_UI. wait60 e wifi-reset continuaram em Can't connect; wait10 e airplane-cycle ficaram no onboarding; wait30/profile-after-wait sofreram instabilidade do Pixel Launcher. profile-after-restart exibiu feed real, mas ainda com Resource downloading.

## Evidência decisiva
restart-after-nav FINAL_UI contém conteúdo real ("Follow", métricas) + Home/Discover/Inbox/Profile e não contém o gate. O run focado 37378882974, independentemente, também estabilizou feed real após adaptive.

## Consequência
A próxima sequência deve usar adaptive -> detectar barra principal -> force-stop/relaunch -> aguardar feed real -> Profile sem coordenada cega quando possível. Não repetir wait/wifi/airplane como correção principal.
