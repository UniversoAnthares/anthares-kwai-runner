# Stabilized autologin still fails before credential entry
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37379608085
JOB: 111997876792
COMMIT: 651d9924beb570b02ad08b252533d28695a4d75c
SUPERSEDES: test-hub/findings/20261005-2216-stabilized-autologin-running.md

## Objetivo
Testar autologin real após incorporar restart-after-nav, alteração causal comprovada na estabilização.

## Resultado
Android, vault, credenciais presentes, instalação e launch passaram. ANDROID_EXECUTOR_ACCEPTED foi emitido. Mesmo com a estabilização nova, o autologin terminou AUTOLOGIN_FAILED_RC=3 após cerca de 5m43s na fase de UI. RC=3 significa que nenhum campo editável de conta foi encontrado. O auth probe não executou.

## Evidência decisiva
Log do job 111997876792: KWAI_LAUNCHED; ANDROID_EXECUTOR_ACCEPTED; AUTOLOGIN_FAILED_RC=3; exit code 3. Não houve senha incorreta nem challenge. As credenciais não foram a causa observada.

## Consequência
Não repetir autologin credenciado até identificar o controle/tela que realmente abre o formulário. A estabilização resolveu outro problema, mas não resolve a descoberta do formulário. Próximo teste deve ser não credenciado, curto, instrumentando árvore UI após Profile e registrando texto/resource-id/class/clickable/bounds por transição. Depois alterar o seletor com base nessa evidência.
