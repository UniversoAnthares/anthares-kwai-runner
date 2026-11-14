# Agent04 — Kwai Lite íntegro; cadastro e execução SpawnDroid bloqueados por formato do artefato
STATUS: PARTIAL
AREA: kwai-lite-readiness
DATE: 2026-11-14
OWNER: agent04-chatgpt
SUPERSEDES: 20261114-agent04-lease-kwai-lite-readiness.md
LEASE_CLOSED: 20261114-agent04-lease-kwai-lite-readiness.md
REPO_BASELINE: 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
GITLAB_PEER: UniversoAnthares/anthares-kwai-runner main 3c001d5fb4c955e2d6c7c604080b8021f227b901 (defasado)
PUBLICATION_ATTEMPTED: false
COST_ADDITIONAL_BRL: 0
DEVICE_MINUTES_CONSUMED_BY_AGENT04: 0

## Evidência confirmada
- Extratos ADB de Android físico do próprio titular: `kwai.lite.video`, 18 APKs, 135708824 bytes em conjunto, manifesto JSON original. Tamanho e SHA-256 recalculados para cada um: **18/18 iguais**, divergências 0. `base.apk` SHA-256 `56dfa923bc41cdb51d9c56ae4d7cebe8f59fa81fda8ef0ba0352b04a15ad571b`.
- `adb shell dumpsys package kwai.lite.video` confirmou `versionCode=647120`, `versionName=13.10.10.647120`, `minSdk=21`, `targetSdk=36`.
- Leitura independente do APK Signing Block v2 (0x7109871a) e v3 (0xf05368c0), em todos os 18 arquivos: certificado SHA-256 idêntico `bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047`. O fingerprint corresponde à referência pública de assinatura do Kwai no APKMirror. Extração de certificado e validação do manifesto não substituem um `apksigner verify` integral.
- Consulta autenticada e de somente leitura ao `GET /api/apps` no workspace SpawnDroid: HTTP 200, apenas um aplicativo `spawndroid-demo-ae64feef92`; nenhum `kwai.lite.video` ou `com.kwai.video` registrado naquele snapshot. `GET /api/sessions`: três sessões históricas associadas apenas à demo, todas com `endedAt` registrado. `GET /api/device-profiles`: `android-14-phone` disponível.
- Contrato oficial SpawnDroid: `POST /api/apps` aceita arquivo `.apk` ou `.aab`; AAB é convertido pelo host em APK universal. O lote existente é de splits extraídos do aparelho, não um AAB nem um APK universal demonstrado.
- Repositório: `tools/kwai_spawndroid_probe.py` e `tools/kwai_spawndroid_stable_hub.py` exigem `com.kwai.video`; AGENTE 02 tem PR #2609 para reforçar verificação W3C da conta regular.
- Histórico independente: `20261113-kwai-three-posts-confirmed-oneoff-revoked-neon76.md` comprova duas URLs de `@lucasrosalem` e uma de `@universoanthares` em outros executores, com dedupe Neon. Nenhuma dessas publicações é prova do SpawnDroid. Isolamento SQL por RLS continua UNPROVEN.

## Bloqueio e próximos critérios de aceite
1. AGENTE 01 ou outra rota autorizada precisa obter APK universal original e legitimamente assinado do pacote `kwai.lite.video`, ou AAB legítimo do publicador; validar fingerprint, pacote, versão e integridade integral antes de enviar. Reempacotar os 18 splits com chave diferente invalida a procedência exigida.
2. Registrar apenas o build validado no SpawnDroid e conferir `app.slug` e `packageName` em `GET /api/apps`. O slot Hobby é compartilhado com os AGENTES 01–03; lease e inventário antes de iniciar, sem consumo pago.
3. Configuração de conta estritamente segregada: `kwai.lite.video` -> `kwai:lucasrosalem` -> `@lucasrosalem`; Kwai regular `com.kwai.video` -> `kwai:universoanthares` -> `@universoanthares`. Não compartilhar autenticação, perfil, ledger ou arquivos de vídeo; utilizar `target_key` na deduplicação e reconciliar antes de qualquer envio.
4. AGENTES 05/06: manter `cloud_cutover.enabled=false` e publicadores existentes, não declarar publicação cloud. Validar o fluxo após cadastro real e login legítimo; exigir 1 URL de vídeo NOVO emitido pelo runner SpawnDroid para a conta exata, recibo Neon e confirmação de encerramento do dispositivo.
5. Não há ID de artefato Kwai Lite, identidade autenticada no Android cloud, MP4 de teste, URL de teste nem sessão do Agent04 encerrada, porque nenhuma sessão do Agent04 foi iniciada. Consumo incremental desta tarefa: 0.

## Fontes externas
- SpawnDroid API: https://docs.spawndroid.io/docs/api/
- Quickstart: https://docs.spawndroid.io/docs/quickstart/
- Pricing: https://spawndroid.io/pricing/
- Kwai Lite oficial (Play): https://play.google.com/store/apps/details?id=kwai.lite.video

## Preservação
Sem alterações de fila/Neon, sem publicação, upload, login, criação de dispositivo, compra, migração, cutover ou alterações em publicadores. O único efeito proposto neste PR é documentação de evidência.
