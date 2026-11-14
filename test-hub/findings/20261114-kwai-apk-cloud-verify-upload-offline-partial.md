# SpawnDroid item 1 — verificador cloud implementado e homologado em CI
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43615064225
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43615064225/job/132508199111
COMMIT: 84b41d3f63b14ae3ed0d62ad4302042ea6b40c6b
SUPERSEDES: 20261114-kwai-apk-cloud-verify-upload-running.md
OWNER: ChatGPT item1 (branch isolada)

## Objetivo
Concluir uma rota de validação criptográfica de um APK universal legítimo e cadastro posterior no SpawnDroid, sem armazenamento do artefato no PC.

## Resultado de implementação
- Script `tools/kwai_spawndroid_apk_guard.py`: SHA256 integral do binário, ZIP, pacote exato `com.kwai.video`, versão >= 647004, arquitetura ARM64 quando declarada, `apksigner verify --verbose --print-certs` v2/v3 com SHA256 de certificado oficial `bb8d2610...`.
- API de registro opcional com autorização explícita: inventário, presign para PUT cloud, upload único, POST /api/apps, readback GET /api/apps, rejeição de pacote/slug divergente, bloqueio de tentativa incerta.
- Workflow GitHub-hosted com download de URL HTTPS permitida, limpeza do arquivo temporário, nenhuma mídia armazenada no Windows, nenhuma sessão Android e nenhum corte de produção.
- PR draft #2616, separado do PR do Agente 01 #2611; GitLab peer não espelhado.

## Evidência decisiva
- Run 43615064225 job 132508199111: `Ran 16 tests in 0.042s`, `OK`.
- `SPAWNDROID_APK_GUARD_SYNTHETIC_CONTRACT=PASS`.
- `SPAWNDROID_REGISTRATION_DEFAULT_DISABLED=PASS`.
- `KWAI_SPAWNDROID_APK_GUARD_NO_CUTOVER=PASS`.
- Job de download e upload: `skipped` (workflow_dispatch não iniciado). Nenhum APK real foi obtido neste teste.
- Download de catálogo Uptodown apresentou desafio Cloudflare no navegador cloud; tentativa de solução terminou em timeout; sessão encerrada. Nenhuma forma de contorno foi utilizada.
- Candidato de fonte pública para teste posterior: `com.kwai.video`, 13.9.30.647004, APK anunciado de 192.61 MB, SHA256 declarado `f11e82aa1e690e8fc0d105dceec8111791e408b617214a6c55c5fdf506ebc168`; bytes ainda não obtidos, logo não certificado.

## Limites
- `OFFLINE_PROVEN` somente para a lógica, usando assinatura e APK sintéticos mockados. Jamais chamar essa prova de APK oficial homologado.
- `REAL_APK_NOT_OBTAINED`: falta arquivo universal original de distribuição legítima.
- `APP_SIGNING_UNVERIFIED`: falta executar apksigner sobre o APK real.
- `SPAWNDROID_APP_NOT_REGISTERED`: falta upload API e slug em inventário autenticado.
- Sem consumo de minutos Android, login ou publicação.
- Manter `cloud_cutover.enabled=false` e publicadores existentes; não promover PR automaticamente.

## Próximos passos
1. Obter URL HTTPS legítima para download direto de APK universal, sem contornar restrições do distribuidor.
2. Acionar a validação em executor GitHub-hosted após aprovação de revisão e existência do workflow na branch padrão; conferir SHA256 original, pacote, arquitetura e assinatura.
3. Providenciar chave `SPAWNDROID_API_KEY` de escopo `upload` ou usar console autenticado autorizado para registrar; registrar uma única vez, confirmar `app.slug` por readback.
4. Só então liberar o AGENTE 02 para canário Android real, respeitando cota e slot do Hobby.
