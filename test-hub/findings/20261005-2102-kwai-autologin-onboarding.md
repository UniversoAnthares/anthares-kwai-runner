# Autologin blocked by onboarding
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37370733856
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Autenticar automaticamente no Kwai com KWAI_LOGIN e KWAI_PASSWORD.

## Resultado
Instalação e abertura funcionaram, mas o fluxo procurou o campo de login cedo demais. A UI ainda estava em permissão/onboarding. Resultado AUTOLOGIN_FAILED_RC=3.

## Evidência decisiva
Artefatos e logs mostraram onboarding/permission antes da tela de login.

## Consequência
Não repetir o mesmo autologin. Primeiro atravessar deterministicamente permissões/onboarding e só então detectar/preencher login.
