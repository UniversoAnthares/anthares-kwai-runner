# AGENTE 02: WebDriver hub prova de estado e teardown
STATUS: RUNNING
AREA: android
DATE: 2026-11-14
RUN: none
JOB: agent02-spawndroid-webdriver-proof-20261114
COMMIT: 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
SUPERSEDES: none

## Objetivo
Conferir o protocolo W3C/Appium, a leitura do estado do aplicativo e a confirmação de término do WebDriver antes de admitir canário real.

BASELINE_PROVEN: PRs #2605 #2606 #2607 incorporados em main. Integração offline existe; prova Android real e sessão fechada ainda ausentes.
FAILED_AVOIDED: sem chamada POST /session até verificar credenciais, APK registrado, cota Hobby e runner livre no workspace autenticado.
SUCCESS_SIGNAL: testes offline validam consulta foreground, XML e rejeição de fechamento sem readback. Homologação real separada.
FAILURE_SIGNAL: código permite sucesso sem estado foreground ou sem término de sessão; ou cria sessão real inadvertidamente.
TEST_VALIDITY: validação estática/offline exclusivamente, sem consumir minutos e sem tocar publicadores.

## Execução
Branch isolada. GitLab peer em main consultado: caminho do adaptador ausente (espelho defasado). Sem espelhamento automático, sem alteração em filas ou produção.
