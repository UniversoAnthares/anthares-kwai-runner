# SpawnDroid: auditoria de APKs, formatos aceitos e catálogo autenticado
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: Anthares Remote inspection (read-only), inventory job 062892e8d424d6aa
COMMIT: this finding
SUPERSEDES: none

## Objetivo
Identificar e registrar um APK universal do Kwai legítimo e compatível com o SpawnDroid, sem alterar assinatura, publicadores ou contas existentes.

## Resultado
- O manifesto de extração ADB do `com.kwai.video` contém 25 APKs, totalizando 202108730 bytes. Recomputação SHA-256 de todos os 25 arquivos: 25/25 correspondentes ao manifesto.
- O manifesto de `kwai.lite.video` contém 18 APKs, totalizando 135708824 bytes. Recomputação SHA-256: 18/18 correspondentes. Total 43/43.
- Referência externa do certificado Kwai, SHA-256: `bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047` (APKMirror 13.10.10.647103); correspondência de certificado, isoladamente, não é verificação criptográfica completa por apksigner.
- Documentação SpawnDroid confirma APK universal ou AAB, limite 512 MB, ARM64; split APKs sem suporte. Não converter splits em um APK por reempacotamento e assinatura própria.
- Workspace autenticado `Universo anthares`, Hobby ativo: catálogo exibiu exclusivamente `io.spawndroid.demo`; 1 artifact; 0/1 sessões em execução. Nenhum `com.kwai.video` cadastrado ou slug válido.
- Painel API & CI/CD exibiu zero chaves de API no momento da inspeção.
- APKMirror lista APK individual `com.kwai.video` 10.6.10.536002 (09/07/2024, 245.72 MB), porém a versão está defasada em mais de dois anos; exige avaliação de APIs, login e funcionalidades antes de homologar. Outras versões modernas indexadas são bundles. APKCombo apresenta informação inconsistente para 13.8.30.646601 (APK de 192 MB ou XAPK); não selecionar sem obter bytes e verificar assinatura.
- Teste local somente com mocks: `python -B -m unittest discover -s tests -p test_kwai_spawndroid_probe.py -v`: 11 testes OK, exit code 0. Nenhuma sessão Android aberta ou publicação iniciada nesta auditoria.
- Os workflows já recebem o identificador via `workflow_dispatch.inputs.artifact_slug` (Hub) e `workflow_dispatch.inputs.artifact_id` (preflight). Nenhuma alteração de roteamento é necessária antes do cadastro.

## Evidência decisiva
- Catálogo: `1 artifact` / `io.spawndroid.demo` / `Live now 0 / 1`.
- Auditoria: `PKG=com.kwai.video COUNT=25 BYTES=202108730 FAIL=`; `PKG=kwai.lite.video COUNT=18 BYTES=135708824 FAIL=`.
- Assinatura de terceiros: https://www.apkmirror.com/apk/joyo-technology-pte-ltd-2/kwai-short-video-maker-community/kwai-video-drama-13-10-10-647103-release/
- Restrições oficiais: https://docs.spawndroid.io/docs/quickstart/ e https://docs.spawndroid.io/docs/api/
- Distribuição individual antiga: https://www.apkmirror.com/apk/joyo-technology-pte-ltd-2/kwai-short-video-community/variant-%7B%22arches_slug%22%3A%5B%5D%2C%22dpis_slug%22%3A%5B%22nodpi%22%5D%7D/

## Consequência e handoff AGENTE 02
`SPAWNDROID_KWAI_ARTIFACT_SLUG=UNCONFIRMED` e `SPAWNDROID_KWAI_ARTIFACT_ID=UNCONFIRMED`. Nenhum slug deve ser presumido nem usado para iniciar sessões. Próximo passo: obter um APK individual atual de fonte confiável, executar `apksigner verify --verbose --print-certs` em cada artefato candidato, verificar identidade original e SHA-256 do arquivo integral; somente então cadastrar no workspace e comprovar o `app.slug` pela API/painel. Preservar produção e `cloud_cutover.enabled=false`. Sem evidência de upload, assinatura plena ou implantação concluída.
