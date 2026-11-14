# SpawnDroid item 1 — splits originais via Appium: contrato offline comprovado
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43622425772
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43622425772/job/132530836887
COMMIT: e5b9c842429c71e06598e7af549cb880dfce3ca9
SUPERSEDES: 20261114-spawndroid-original-split-appium-exploration-running.md
OWNER: ChatGPT item1 / PR #2616

## Provas
- 16 testes anteriores do guard de APK único e 20 novos testes de contrato de splits: `Ran 16 tests... OK`, `Ran 20 tests... OK`; GitHub Actions hosted Ubuntu; `KWAI_SPAWNDROID_APK_GUARD_NO_CUTOVER=PASS`.
- `tools/kwai_spawndroid_original_splits.py` confere manifestos, pacotes oficiais, hashes completos, versão, assinatura v2/v3 por apksigner, URLs HTTPS aprovadas e contagem exata dos splits de cada conta.
- Contrato `mobile: installMultipleApks` usa exclusivamente sessão Appium existente e confirmação de pacote/versão por `isAppInstalled` e `listApps`. Executar sem `SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED=1` é impedido.
- Documentos oficiais: https://appium.github.io/appium-uiautomator2-driver/latest/reference/execute-methods/ e https://docs.spawndroid.io/docs/guides/appium-capabilities-android/ . Appium 3 e UiAutomator2 8.x documentados pelo provedor.

## Limite de prova
TEST_VALIDITY: SINTÉTICO / OFFLINE. O suporte genérico Appium ainda não comprova que a implementação hospedada SpawnDroid permite installMultipleApks. Nenhuma sessão criada, nenhuma instalação remota ou publicação feita. O upload de builds SpawnDroid permanece limitado a APK universal/AAB. Para usar splits, requer arquivo original disponível por URLs HTTPS autorizadas na nuvem, sessão portadora com lease e quota, verificação da assinatura real de todos os componentes pelo runner e prova terminal do dispositivo.

## Consequência
Manter item1 PARTIAL, `cloud_cutover.enabled=false`, PR draft #2616 e publicadores atuais. Coordenar canário com AGENTE02 quando os 25 arquivos originais estiverem acessíveis de fonte cloud autorizada, sem usar o PC como staging.
