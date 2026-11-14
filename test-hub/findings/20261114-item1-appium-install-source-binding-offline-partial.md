# Item 1 — Appium só admite splits verificados e URLs vinculadas
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43625427459
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43625427459
COMMIT: 9232f18232b247da2a6fac1006e59dabeb71b060
SUPERSEDES: 20261114-item1-appium-install-source-binding-running.md
OWNER: ChatGPT item1; PR draft #2616

## Resultado implementado
- `webdriver_script` agora exige `GITHUB_ACTIONS=true`, `RUNNER_TEMP` e canário explicitamente habilitado; diretório comprovado dentro de uma subpasta efêmera do runner.
- Antes de qualquer chamada Appium, exige manifesto completo com URLs HTTPS em host autorizado, pacote/versão corretos, igualdade exata da lista ordenada de URLs e auditoria local de TODOS os arquivos com SHA-256, ZIP, pacote e apksigner original v2/v3 (por `audit_downloaded_set`).
- O recibo é conferido contra pacote, versão, número de componentes, quantidade de bytes e impressão digital do certificado. URLs alteradas, fonte não auditada, pacote divergente, assinatura inválida ou execução fora de cloud encerram sem instalar.
- `mobile: installMultipleApks`, `isAppInstalled` e `listApps` só executam depois dessas barreiras. Instalação remota permanece condicionada a uma sessão legítima já coordenada pelo Agente 02, sem início/teardown nesta função.
- Um risco residual permanece: o Appium remoto obtém os APKs das URLs em outro instante. O armazenamento de origem deve ser imutável e exigir links de acesso autorizados até o final da instalação.

## Evidência local real (somente leitura)
- ARA Windows: `D:\AntharsWork\spawndroid-preflight-qa\verified-packages\com.kwai.video`: 25 arquivos, 25 tamanhos e SHA-256 coerentes com manifesto, 0 divergência.
- ARA Windows: `...\kwai.lite.video`: 18 arquivos, 18 tamanhos e SHA-256 coerentes, 0 divergência.
- A manifestação local contém `package`, `split_count` e `files`, mas carece de `versionCode` e de URLs HTTPS temporárias. Logo a compatibilidade de transporte cloud ainda requer implementação.
- Android SDK `aapt/apksigner` não foi identificado no PATH ou nos caminhos locais usuais. Assinatura v2/v3 real deve ser comprovada no GitHub-hosted runner quando arquivos forem acessíveis por HTTPS.

## Evidência CI
- Run 43625427459, job offline-contracts `success`: `Ran 16 tests... OK` para APK universal e `Ran 28 tests... OK` para splits. Total 44.
- Sinais: `KWAI_SPLITS_DEFAULT_NO_ANDROID_SESSION=PASS`, `KWAI_SPLITS_REGULAR_MANIFEST=PASS`, `KWAI_SPLITS_LITE_MANIFEST=PASS`, `KWAI_SPLITS_APPIUM_W3C_CONTRACT=PASS`, `KWAI_SPAWNDROID_APK_GUARD_NO_CUTOVER=PASS`.
- O job de upload real ficou `skipped`. Testes usam mocks sintéticos; nenhuma API SpawnDroid de mutação, dispositivo, login ou publicação foi executada nesta rodada.

## Estado e próxima dependência
TEST_VALIDITY: OFFLINE_PROVEN only. ITEM_1=PARTIAL. Sem APK universal disponível; teste APKMirror 2024 anterior recusou HTTP 403. Falta fonte privada temporária HTTPS acessível pelo host SpawnDroid para os 43 APKs originais, prova de assinatura real de cada componente em runner cloud, canário com sessão existente/lease/quota do Agente 02, readback de pacote instalado e teardown. Sem `app.slug` Kwai no inventário comprovado. Preservar publicadores atuais e `cloud_cutover.enabled=false`.
