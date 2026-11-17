# Distribuições distintas com mesma versão: candidata com pacote correto, ainda sem validação binária
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: Agente 01; verificação do catálogo APKMirror
COMMIT: this finding
SUPERSEDES: none

## Objetivo
Distinguir variantes homônimas do Kwai 10.6.10.536002 e identificar uma candidata íntegra para SpawnDroid sem confundir pacote ou certificado.

## Resultado
Há duas fichas APKMirror da versão 10.6.10.536002 com identidades Android **diferentes**:
1. Caminho `kwai-short-video-community`: `com.kwai.kuaishou.video.live`, certificado SHA-256 `588774ea798843484c7100da2450005090522fda0dcb64be01c04079349c0acc`, rejeitada (ver finding que corrigiu a triagem inicial).
2. Caminho `kwai-short-video-maker-community`: `com.kwai.video`, certificado SHA-256 publicamente informado `bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047`, APK individual ARM64 + ARMv7, 255956802 bytes, SHA-256 do binário publicado `76e6a6208f3979e0e6e69807160d7fe9d3b0ef97c82f6980933eb775616b4b58`. Candidata documental, ainda não auditada por `apksigner`.

## Evidência decisiva
- URL exata da candidata com pacote correto: https://www.apkmirror.com/apk/joyo-technology-pte-ltd-2/kwai-short-video-maker-community/kwai-short-video-maker-community-10-6-10-536002-release/kwai-watch-cool-videos-10-6-10-536002-2-android-apk-download/
- A página informa indisponibilidade de download em certos casos por pedido de retirada feito por desenvolvedores. Nenhum download ou envio efetivado.

## Riscos explícitos e decisão
- Publicação datada 09/07/2024: versão 28 meses anterior à data 14/11/2026. Alto risco de expiração de API, login, TLS, requisitos de segurança, funcionalidades de publicação e compatibilidade servidor.
- A compatibilidade de instalação Android 12-16 é plausível em razão do minSDK 21 e arm64, porém não testada neste arquivo.
- A assinatura original e SHA-256 do APK ainda requerem verificação independente dos **bytes baixados**; a publicação de hashes em catálogo é só referência de comparação, nunca verificação executada.
- Sem entrega validada do binário, sem upload ao SpawnDroid, sem app.slug confirmado. O workflow continua gated, `cloud_cutover.enabled=false` e contas preservadas.

## Handoff AGENTE 02
`SPAWNDROID_KWAI_ARTIFACT_SLUG=UNCONFIRMED`; candidato *documental* com URL acima, pacote correto e hash esperado. Exigir download autorizado, SHA-256 real, apksigner, avaliação formal de compatibilidade por versão antes do cadastro. Aplicativo mais recente em splits continua preferido se SpawnDroid passar a suportar esse formato oficialmente.
