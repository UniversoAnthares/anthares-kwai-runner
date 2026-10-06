# QA: first valid Anthares Android Agent build reaches compilation and produces APK artifact
STATUS: PROVEN
AREA: android
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37397385606
JOB: 112056483320
COMMIT: 3d93780c6742df2903fe6d83bc93f3ffde47ecc5
SUPERSEDES: test-hub/findings/20261005-2102-qa-android-agent-build-harness-invalid.md

## Objetivo
Fechar o item QA de obter e classificar o primeiro build realmente válido do Android Agent depois das falhas de harness em setup-android.

## Resultado
PROVEN. O workflow corrigido usou o SDK hospedado, alcançou a etapa real `Build agent`, terminou com sucesso e publicou o APK debug como artifact. Portanto a fundação Android compila; as falhas anteriores eram exclusivamente do harness.

## Evidência decisiva
Run 37397385606 / job 112056483320: checkout, Java, Gradle setup, `Build agent` e upload-artifact concluíram success. Artifact `anthares-android-agent-debug`, id 11384550256, size 8276 bytes, digest sha256:727a9f8b33f3f952a362984ac4550bb2b55f410f91f7bd58bf86c5e2ef014162.

## Consequência
O item de QA `primeiro build válido do Android Agent` está encerrado. Não repetir testes do antigo setup-android. Próxima cadeia causal é runtime Android/instalação/Accessibility/Kwai, que é distinta de build e deve respeitar lease kwai-login antes de qualquer mutação.