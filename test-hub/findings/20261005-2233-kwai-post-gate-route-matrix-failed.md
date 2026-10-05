# Post-gate route matrix failed to reach login control
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381528807
JOB: matrix
COMMIT: 7d2a1eb40083d44219081ca309fd872ba800ad3f
SUPERSEDES: none

## Objetivo
Explorar rotas posteriores ao gate/main navigation para transformar a navegação Home/Discover/Inbox/Profile em acesso real ao login.

## Resultado
O run terminou failure. A maioria das variantes encerrou com RESULT=NO_MAIN_NAV (exit 20). Algumas variantes alcançaram a navegação principal, porém continuaram exibindo resource downloading e não comprovaram controle de login. parent-twice terminou verde com FINAL_UI contendo "can't connect to server", Home/Discover/Inbox/Profile e resource downloading. parent-restart também terminou verde e chegou a uma tela de perfil/conteúdo com Follow e contadores, ainda acompanhada de resource downloading. Portanto, verde nesses jobs não equivale a login encontrado.

## Evidência decisiva
parent-twice: FINAL_UI="can't connect to server ... home discover inbox profile resource downloading". parent-restart: FINAL_UI contém Follow, contadores, Home/Discover/Inbox/Profile e resource downloading. parent-restart-wait, parent-discover-profile, parent-now, parent-wait15, parent-wait30, parent-hide-resource, parent-inbox-profile, parent-scroll-up, parent-wait-resource e parent-coordinate registraram RESULT=NO_MAIN_NAV nas execuções observadas.

## Consequência
Não repetir esta matriz. A pista mais forte passa a ser parent-restart: ele alcançou conteúdo de perfil. O próximo teste deve partir dessa rota e inspecionar a tela de perfil alcançada, procurando ações de conta/login por texto, content-desc e resource-id, incluindo menu/configurações, em vez de esperar indefinidamente resource downloading. O harness deve considerar sucesso somente quando encontrar um controle de autenticação ou campo editável.
