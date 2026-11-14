# Correção da seleção de APK individual: pacote e certificado incompatíveis
STATUS: FAILED
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: Agente 01; inspeção documental de integridade
COMMIT: this finding
SUPERSEDES: test-hub/findings/20261114-spawndroid-kwai-apk-official-distribution-partial.md

## Objetivo
Revisar a candidatura de um APK único do Kwai 10.6.10.536002 indicado pelo catálogo APKMirror, antes de qualquer download ou upload.

## Resultado
O detalhamento do APKMirror identifica a versão 10.6.10.536002 como pacote `com.kwai.kuaishou.video.live`, com SHA-256 do certificado `588774ea798843484c7100da2450005090522fda0dcb64be01c04079349c0acc`. A exigência contratual do projeto é `com.kwai.video` e certificado de referência `bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047`. O aplicativo da versão de 2024 é INELEGÍVEL para cadastro. Não baixar, não assinar, não publicar nem cadastrá-lo.

## Evidência decisiva
Detalhes do binário e assinatura do APKMirror:
https://www.apkmirror.com/apk/joyo-technology-pte-ltd-2/kwai-short-video-community/kwai-short-video-community-10-6-10-536002-release/ (consultar os dados do variant e do cert)
Busca pela fonte oficial do pacote requerido: https://www.apkmirror.com/apk/joyo-technology-pte-ltd-2/kwai-short-video-maker-community/kwai-video-drama-13-10-10-647103-release/kwai-video-drama-13-10-10-647103-android-apk-download/ , informa BUNDLE 7 S, não APK universal.

## Consequência e handoff ao AGENTE 02
Preservar `SPAWNDROID_KWAI_ARTIFACT_SLUG=UNCONFIRMED`. O workspace continua contendo apenas `io.spawndroid.demo` na última inspeção. A obtenção e validação criptográfica completa de um APK universal legítimo `com.kwai.video` continuam pendentes. Versões contemporâneas em APKMirror estão em formato BUNDLE e não são elegíveis para envio individual ao SpawnDroid. O commit original é evidência histórica parcial; este finding é a correção autoritativa. Nenhuma conta, publicador ou dispositivo operacional foi alterado.
