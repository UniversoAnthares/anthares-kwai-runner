# AGENTE 02 — SpawnDroid: validação de contratos offline e canário real pendente
STATUS: PARTIAL
AREA: android
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596034043
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596034043/job/132450601457
COMMIT: 218dc085bdbfa2d2616d343473e28213ad431646
SUPERSEDES: 20261114-agent02-spawndroid-webdriver-proof-running.md

## Objetivo
Diferenciar sucesso de comando Appium, abertura real do app, fechamento da sessão W3C e encerramento da reserva do provedor.

## Resultado
Na PR #2609: verificações da capability de Android, consulta foreground Kwai, XML UI, readback W3C terminal; testes negativos de pacote incorreto e DELETE sem prova final. Grupo de concorrência alinhado entre workflows. Sem sessão real, sem publicação, sem credenciais expostas.

## Evidência decisiva
Hub run 43596034043: `Ran 10 tests ... OK`; compile success; `remote-canary` skipped. API preflight run 43596034080 completed/success, somente testes offline. Não houve alocação Android nem gasto de minutos por essas duas execuções.

## Consequência
SUCCESS_SIGNAL: testes offline de contratos e readback W3C passaram.
FAILURE_SIGNAL: canário real continua bloqueado sem APK autenticado, saldo e ausência de sessão simultânea; não há prova de ARM64 ou término no provedor.
TEST_VALIDITY: exclusivamente unitários simulados em GitHub Actions; resultado PARTIAL. Não usar como homologação real nem ativar produção.
Referência de handoff: docs/KWAI-SPAWNDROID-AGENT02-HANDOFF-20261114.md.
