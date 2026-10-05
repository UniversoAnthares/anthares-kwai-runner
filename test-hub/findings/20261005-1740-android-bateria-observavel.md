# Bateria observável 01-07 e limites da evidência
STATUS: PARTIAL
AREA: android
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37377426655
JOB: multiple
COMMIT: none
SUPERSEDES: none

## Objetivo
Expor componentes do executor Kwai como jobs independentes e facilmente fiscalizáveis.

## Resultado
Os jobs 01 BOOT, 02 INSTALLER, 03 PERMISSIONS, 04 ONBOARDING e 05 UI MAP ficaram verdes. Os jobs 06 AUTOLOGIN E2E e 07 AUTH PROBE também ficaram verdes, mas eram apenas gates informativos e NÃO executaram autenticação real.

## Evidência decisiva
O run 37377426655 concluiu os cinco checks de componente com success. Os jobs 06 e 07 executaram somente mensagens informativas, portanto não são prova de login nem de sessão autenticada.

Evidências históricas relacionadas: run 37370378251 chegou a KWAI_LAUNCHED/ANDROID_EXECUTOR_ACCEPTED e falhou AUTOLOGIN_FAILED_RC=3; run 37370733856 repetiu RC=3; evidência posterior identificou permission dialog; run 37371976406 mostrou onboarding 1/11 com controles icon-only.

## Consequência
Considerar 01-05 apenas evidência técnica de seus componentes. Não marcar autologin/auth como PROVEN até um teste real autenticado. Não diagnosticar novamente Android, vault, split selection ou launch como causa sem nova evidência que contradiga os testes já comprovados.
