# Corrected login metadata v2 did not test manifest hypothesis
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37385599522
JOB: 112017974045
COMMIT: 845ab9455a173511a4fce368a8b9d52c6076c8fe
SUPERSEDES: test-hub/findings/20261005-1904-kwai-login-activity-metadata-corrected-running.md

BASELINE_PROVEN: test-hub/findings/20261005-1858-kwai-login-activities-crossref.md
FAILED_AVOIDED: the earlier aapt false-green remains invalid and must not be reused.
SUCCESS_SIGNAL: manifest metadata for a known login component.
FAILURE_SIGNAL: valid parser proves known DEX login classes are absent from manifest components.
TEST_VALIDITY: probe script must exist and execute before any manifest conclusion.

## Objetivo
Auditar o RUNNING antigo e determinar se a hipótese de metadata chegou a ser testada.

## Resultado
TEST INVALID. O run terminou failure antes do probe: o workflow tentou executar kwai_login_activity_metadata_v2.sh, mas o arquivo não existia no checkout. Nenhuma conclusão sobre exported/enabled/intent-filter foi produzida.

## Evidência decisiva
Job 112017974045: `bash: kwai_login_activity_metadata_v2.sh: No such file or directory`; exit code 127; nenhum artifact de metadata foi gerado.

## Consequência
CHAT 1 deve preservar a hipótese como UNKNOWN e não usar este run como evidência contra as Activities. Antes de qualquer direct Activity, corrigir causalmente a presença/caminho do script e executar um único probe válido.