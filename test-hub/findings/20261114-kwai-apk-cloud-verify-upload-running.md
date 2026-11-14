# Kwai SpawnDroid — verificador de APK e upload cloud isolado
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: ChatGPT item1 — branch feature/spawndroid-kwai-apk-verified-upload-20261114
COMMIT: initial base 29663af69e50f0a74cba6199e73d16c6ed784b7d
SUPERSEDES: none
OWNER: item1-apk-guard, separate from AGENTE01 documentation-only PR #2611
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- 25 Kwai splits e 18 Lite splits possuem SHA256 coerente nos manifestos, porém não são um APK universal original.
- Workspace SpawnDroid Hobby continha somente demo em leitura autenticada anterior; sem app.slug Kwai comprovado.
- Documentação oficial: POST /api/apps/presign, PUT storage, POST /api/apps; upload não inicia dispositivo.
- PR #2611 documenta candidatos e bloqueio do arquivo; PR #2609 implementou safety WebDriver na main.
- Novo candidato documental Uptodown APK único com.kwai.video versão 13.9.30.647004, 192.61 MB, SHA256 declarado f11e82aa1e690e8fc0d105dceec8111791e408b617214a6c55c5fdf506ebc168.

## FAILED_AVOIDED
Não reempacotar splits com nova assinatura; não usar APK de pacote distinto; não repetir download por desafio de segurança; não guardar APK no PC; não registrar artefato sem SHA256+apksigner+aapt.

## SUCCESS_SIGNAL
- Novo validador cloud com cobertura offline de package/version/arquitetura/assinatura/hash; testes unitários GitHub Actions PASS.
- Registro no SpawnDroid somente após binário verdadeiro recebido e validado; conferir app.slug por readback.

## FAILURE_SIGNAL
Tentativa de registrar pacote diferente ou assinatura divergente; download indisponível/405/403, captcha não resolvido; ausência de segredo upload; estado incerto na API.

## TEST_VALIDITY
Ações de CI com fixtures são OFFLINE_PROVEN apenas para o código. Sem binário baixado e validado, `ANDROID_APK_PROVEN=false`, `SPAWNDROID_UPLOAD_PROVEN=false`. Nenhum dispositivo ou publicação será iniciado. Preservar cloud_cutover.enabled=false.

## Lease e propriedade
Somente novos arquivos tools/kwai_spawndroid_apk_guard.py, tests/test_kwai_spawndroid_apk_guard.py, .github/workflows/kwai-spawndroid-apk-guard.yml e este finding, em branch própria. Agente 01 mantém PR #2611; não editar seus arquivos. GitLab main diverge, sem mirror. Antes de merge, readback e coordenação Test Hub.