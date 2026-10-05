# Login activity metadata corrected run invalid: script absent
STATUS: FAILED
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37385599522
JOB: 112017974045
COMMIT: 845ab9455a173511a4fce368a8b9d52c6076c8fe
SUPERSEDES: test-hub/findings/20261005-1904-kwai-login-activity-metadata-corrected-running.md

## Objetivo
Validar no Manifest os componentes de login já encontrados estaticamente.

## Resultado
TEST INVALID. O workflow chamou kwai_login_activity_metadata_v2.sh, mas o arquivo não existia no commit executado.

## Evidência decisiva
bash: kwai_login_activity_metadata_v2.sh: No such file or directory

## Consequência
A hipótese sobre Activities não foi testada. Corrigir exclusivamente o harness, exigir aapt válido e repetir o mesmo teste causal.
