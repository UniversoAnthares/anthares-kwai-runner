# Post-onboarding stabilization matrix
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378856592
JOB: matrix of 10
COMMIT: fd5ef6b7f82431b43cb8e43d287dc9dc6ce8e837
SUPERSEDES: none

## Objetivo
Explicar e corrigir o estado pós-onboarding em que a navegação principal aparece junto de "Can't connect to server" / "Resource downloading".

## Resultado
Dez experimentos disparados: wait10, wait30, wait60, wifi-reset, airplane-cycle, restart-after-nav, network-check, resource-wait, profile-after-wait e profile-after-restart.

## Evidência decisiva
Run 37378856592 criado.

## Consequência
Aguardar evidência desta matriz antes de atribuir a falha a coordenadas de Profile ou autenticação.
