# Kwai login surface discovery — PWA web view, no native login surface
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-07
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37613550316
JOB: 112604992835
COMMIT: 442ffdc
SUPERSEDES: none

## Objetivo
Descobrir a superfície real de login do Kwai no emulador cloud.

## Resultado
O app `com.kwai.video` abre como `kwai-pwa` (WebView pública). Não há formulário de login nativo acessível via UI Automator. O feed mostra conteúdo público com botões `follow` e usuários como `@snizb105`, `@rmjts665`, `@pauloantoniodi066`. Bottom nav: `home`, `discover`, `inbox`, `profile`. Campos editáveis: zero.

Isso explica por que RC=3 persiste: o caminho atual do app não expõe login nativo nesta build/rota.

## Consequência
Próximo probe deve mudar causalmente para:
1. Activities exportadas declaradas no Manifest (`KwaiAuthActivity`, `UriRouterActivity`, etc.)
2. Deep links `ikwai://login` e variantes
3. Profile bottom nav como possível rota para settings/logout

Não repetir autologin nativo até uma dessas rotas expor um formulário editável.
