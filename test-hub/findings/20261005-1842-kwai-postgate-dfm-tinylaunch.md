# Matrizes pós-gate isolam TinyLaunchActivity e DFM de Profile
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381484913 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381528807 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37381259065
JOB: matrix
COMMIT: 5af43b986bf9e8126783ddd0127ea5ecea4bc292 ; 7d2a1eb40083d44219081ca309fd872ba800ad3f ; 5104be288894bfe9f545a42b0201051f10f34924
SUPERSEDES: none

## Objetivo
Testar em paralelo rotas após Start now/Profile e corrigir inspeção de UI.

## Resultado
A matriz de 16 rotas executou integralmente. Start now alcança main nav, mas Profile continua acionando o DFM "resource downloading". Esperar 60s não resolve. hide+reopen e profile-id-direct podem retornar ao feed real, ainda sem campos editáveis. A matriz pós-gate mostrou apenas parent-twice, parent-restart e dump-activities como jobs verdes; os demais falharam principalmente antes de MAIN_NAV. dumpsys provou que a activity efetivamente resumida continua com.yxcorp.gifshow.tiny.TinyLaunchActivity. O inspector 37381259065 não testou hipótese: quebrou por SyntaxError causado por texto literal \n no script.

## Evidência decisiva
37381484913 module-wait60: resource downloading permanece após 60s, EDITABLE_COUNT=0.
37381484913 profile-id-direct/module-hide-reopen: feed real + nav Profile, EDITABLE_COUNT=0.
37381528807 dumpsys: topResumedActivity=com.kwai.video/com.yxcorp.gifshow.tiny.TinyLaunchActivity.
37381259065: SyntaxError unexpected character after line continuation character.

## Consequência
Não repetir simples espera do DFM nem tratar o inspector quebrado como falha de UI. Investigar em paralelo: componentes/activities/services/providers do APK relacionados a login/profile, estado de pacotes split/DFM, intents/deeplinks internos, e rotas UI pós-restart. Corrigir o SyntaxError antes de reutilizar o inspector.
