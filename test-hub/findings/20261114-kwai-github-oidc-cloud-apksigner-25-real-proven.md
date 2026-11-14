# Item 1 — 25 APKs Kwai oficiais comprovados em GitHub cloud por OIDC + apksigner
STATUS: PROVEN
AREA: android|kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43641732854
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43641732854/job/132590646295
COMMIT: b67db4fdbaf3256e9240254260dea6c06307df04
SUPERSEDES: 20261114-kwai-hostinger-github-oidc-apk-audit-running.md
OWNER: ChatGPT item1, PR draft #2616
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## Objetivo e prova concluída
A Hostinger possui 25/25 APKs originais do pacote `com.kwai.video` versão `13.10.10.647103`, com volume integral `202108730` bytes. Hashes SHA256 dos 25 foram comparados com manifesto extraído do Android físico, e 25/25 certificações independentes v2 foram aprovadas previamente em Hostinger com o script `tools/kwai_apksig_v2_audit.py`.

O pipeline GitHub-hosted (Ubuntu 24.04) solicitou JWT efêmero ao emissor oficial GitHub Actions OIDC, validado no broker PHP da Hostinger (`oidc-broker.php`) por assinatura RS256/JWKS e claims restritos: audience, issuer, repo, ref, workflow_ref, event_name e github-hosted; sub pode usar template personalizado. Nenhuma chave HMAC de longa duração foi copiada ao GitHub. O broker emitiu links de 1500s para `/signed/<expiry>/<HMAC>/<filename>.apk`, com verificação HMAC existente em fetch.php.

O runner baixou TODOS os 25 APKs somente para `RUNNER_TEMP`, verificou SHA256, ZIP, package, versionCode, certificado e assinatura via Android SDK `apksigner verify --verbose --print-certs`, e removeu os arquivos na saída do TemporaryDirectory. O parser foi corrigido para formato `V3.0 Signer`; feature splits foram analisados por `aapt2` quando legacy `aapt` recusou o badging. Não houve reempacotamento ou assinatura nova.

## Evidência decisiva do job
```
KWAI_OIDC_NO_CLOUD_CUTOVER=PASS
Ran 9 tests in 0.004s
OK
Ran 19 tests in 0.024s
OK
KWAI_OFFICIAL_ANDROID_APKSIGNER_AVAILABLE=PASS
KWAI_CLOUD_ORIGINAL_25_APKS_SHA256_AND_APKSIGNER=PASS
KWAI_CLOUD_SOURCE_PACKAGE=com.kwai.video
KWAI_CLOUD_SOURCE_COUNT=25
KWAI_CLOUD_SOURCE_TOTAL_BYTES=202108730
KWAI_CLOUD_SIGNER_CERT_SHA256=bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047
SPAWNDROID_APK_UPLOAD=NOT_ATTEMPTED
SPAWNDROID_ANDROID_SESSION=NOT_ATTEMPTED
KWAI_PUBLICATION_ATTEMPTED=0
SPAWNDROID_DEVICE_MINUTES_USED=0
```
Resultado do job: SUCCESS. 28 testes unitários novos na rota OIDC/apksigner (9+19), além dos contratos anteriores, todos aprovados. Os detalhes de URLs assinadas e JWT nunca foram gravados no repositório ou log de Actions.

## Testes que falharam mas foram superados
O parser antigo esperava exclusivamente `Signer #1`, enquanto Android 37 inclui rótulo `V3.0 Signer`; status sintético anterior não capturava. Corrigido.
`aapt dump badging` antigo recusava `split_basis.apk`; `aapt2` do SDK validou todos os splits; isso é mudança causal, não ignorar os manifestos.
A primeira checagem OIDC exigia `sub` canônico, enquanto a organização usa subject customizado; a validação atual mantém todos os outros claims exatos e a verificação RSA oficial no broker.

## Limites da prova e ações futuras
A prova é `REAL_APK_CRYPTOGRAPHIC_AUDIT=PROVEN` e `CLOUD_DOWNLOAD=PROVEN`. O objetivo completo ITEM1 continua **PARTIAL**: SpawnDroid ainda não tem upload/cadastro `app.slug` do Kwai, o canário original `mobile: installMultipleApks` retornou HTTP500 e novo teste path-only ficou INVALID por CDP indisponível/SSO GitHub expirado antes de criar sessão. O diretório de navegador isolado exige login GitHub; não acessar credenciais de terceiro nem contornar autenticação. Para concluir, restaurar autenticação legítima ou fornecer SPAWNDROID_API_KEY de escopo mínimo, consultar quota e slot, iniciar uma sessão demo/Android autorizada e chamar installMultipleApks usando URLs HMAC path-only da mesma fonte PROVEN; terminar WebDriver e sessão CI, confirmar readback. Registrar artefato real em /api/apps se fornecido APK universal sem perder identidade do publicador.

Nunca promover `cloud_cutover.enabled=false` automaticamente, não ativar publicadores e não confundir assinatura/prova de bytes com instalação/aplicação funcionando. PR #2616 segue draft; esta finding fecha o lease de auditoria de APK OIDC sem autorizar gastar minutos Android.
