# One-shot cloud — auditar APK universal antigo do Kwai sem cadastro
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: a ser gerado em GitHub Actions
JOB: ChatGPT item1; branch feature/spawndroid-kwai-apk-verified-upload-20261114
COMMIT: baseline e5b9c842429c71e06598e7af549cb880dfce3ca9
SUPERSEDES: none
OWNER: item1-apkmirror-archival-oneoff
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
APKMirror publica versão 10.6.10.536002 como APK único de 255956802 bytes, `com.kwai.video`, certificado SHA-256 `bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047` e hash esperado `76e6a6208f3979e0e6e69807160d7fe9d3b0ef97c82f6980933eb775616b4b58`. Link web de download funcional exibido, bytes ainda não auditados. Versão 2024, inelegível para produção até avaliação de compatibilidade.

## FAILED_AVOIDED
Sem download no PC, sem troca de assinatura, sem bypass de bloqueio do distribuidor, sem upload SpawnDroid ou início de Android. Sem tokens secretos na URL. PR #2616 já possui guard de APK e 36 testes unitários offline verdes.

## SUCCESS_SIGNAL
GitHub-hosted runner obtém binário íntegro pela navegação pública padrão; SHA256 76e6..., tamanho exato; `aapt` identifica pacote e versão; `apksigner verify` valida assinatura original e impressão digital correta. Remoção do artefato do runner por finally. Comprovar tudo via logs de CI sem publicar binário.

## FAILURE_SIGNAL
HTTP 403/404, página de desafio, falta do link, SHA divergente, assinatura inválida, APK alterado, orçamento insuficiente; abortar sem retentativas nem meios de contorno. Resultado será PARTIAL/FAILED, sem novo download automático.

## TEST_VALIDITY
Prova de integridade de binário arquivado de 2024 somente, sem comprovação de compatibilidade com servidores Kwai 2026. Sem registro, app.slug, Android, login ou publicação. Esta rotina temporária deve ser retirada do PR após o run; manter demais trabalhos e `cloud_cutover.enabled=false`.

## OWNERSHIP
Somente novos arquivos `test-hub/findings/20261114-apkmirror-official-universal-archival-canary-*.md` e `.github/workflows/kwai-apk-archive-oneoff.yml` na branch #2616; sem tocar agentes 01–07. GitLab main divergente e preservado.