# Stabilization matrix results: restart recovers feed
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378856592
JOB: 111995195964;111995196143;111995196232
COMMIT: fd5ef6b7f82431b43cb8e43d287dc9dc6ce8e837
SUPERSEDES: test-hub/findings/20261005-2200-stabilization-probes-running.md

## Objetivo
Corrigir o estado pós-onboarding "Can't connect to server"/"Resource downloading".

## Resultado
Os 10 jobs do harness concluíram success, mas os estados de UI diferem. restart-after-nav foi o resultado decisivo: após atravessar onboarding, force-stop/relaunch e espera, o Kwai carregou feed real com conteúdo, Follow e Home/Discover/Inbox/Profile, sem "Can't connect to server". profile-after-restart também carregou feed real e navegação, embora ainda exibisse "Resource downloading". Esperar 60s isoladamente não resolveu. network-check mostrou "Network is unreachable" no ping e permaneceu em "Can't connect to server". wifi-reset também não resolveu. wait30/resource-wait/profile-after-wait chegaram a travamento do Pixel Launcher.

## Evidência decisiva
restart-after-nav: FINAL_UI contém conteúdo real + "follow ... home discover inbox profile".
profile-after-restart: conteúdo real + navegação + "resource downloading".
wait60/network-check/wifi-reset: "can't connect to server".
network-check: "connect: Network is unreachable".

## Consequência
Promover restart-after-nav como etapa determinística do fluxo pós-onboarding. Não usar espera passiva, wifi-reset ou ping como correção. Depois do restart, detectar feed/nav real antes de abrir Profile.
