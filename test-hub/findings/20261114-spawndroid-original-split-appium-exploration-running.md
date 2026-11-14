# SpawnDroid item 1 — instalação de splits com Appium (canário bloqueado até prova)
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: ChatGPT item1 — branch feature/spawndroid-kwai-apk-verified-upload-20261114
COMMIT: base 159194fdc4d70ffccf17f2030da840ab4addada2
SUPERSEDES: none
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
OWNER: item1-original-splits-exploration; branch própria e novos arquivos exclusivos

## BASELINE_PROVEN
- Dois conjuntos originais extraídos no dispositivo autorizado: `com.kwai.video` 25 componentes (202108730 bytes) e `kwai.lite.video` 18 (135708824 bytes); SHA-256 dos arquivos verificados contra manifestos locais, certificado v1 indexado `bb8d2610...`; v2/v3 e execução remota ainda não comprovados.
- SpawnDroid só aceita APK universal ou AAB no upload de builds; cadastro atual de Kwai no catálogo continua sem prova.
- Segundo docs oficiais SpawnDroid, o CI usa Appium 3 e UiAutomator2 8.x; documentação oficial Appium confirma `mobile: installMultipleApks` com URLs HTTPS para os splits, sem reassinatura.
- Existe aplicativo de demonstração no workspace, cujo uso como portador de uma sessão remota precisa de autorização e prova. Nenhuma sessão será iniciada neste experimento offline.

## FAILED_AVOIDED
Não modificar/reassinar bundles originais, não instalar APK adulterado, não copiar credenciais, não iniciar Android sem disponibilidade/cota, não criar mídia/staging no PC, não competir com agentes 01-06. Não acessar API de publicação Kwai.

## SUCCESS_SIGNAL
Código isolado com verificação SHA256/assinatura de cada APK em runner cloud, contrato Appium `mobile: installMultipleApks` bloqueado por variável explícita, e testes offline no GitHub Actions comprovando fail-closed. Registro de APK no SpawnDroid só se download universal e assinatura comprovada pelo validador original, independentemente desta alternativa.

## FAILURE_SIGNAL
Assinatura, pacote, lista ou hash divergem; Appium rejeita método; origem remota mutável sem prova; quota indisponível; resultado incerto; abortar sem repetir instalação.

## TEST_VALIDITY
Offline: mocks de assinatura, Appium e rede; teste real SpawnDroid não executado. Após teste de contrato, registrar PARTIAL e exigir prova remota do comando e recibo da sessão sem habilitar cutover.

## LEASE / BRANCH
Owner deste finding: ChatGPT item1. Destinos novos: `tools/kwai_spawndroid_original_splits.py`, `tests/test_kwai_spawndroid_original_splits.py` e extensão pontual do workflow `.github/workflows/kwai-spawndroid-apk-guard.yml` (arquivo da própria branch #2616). Peer GitLab main sem esses arquivos; preservar divergência sem espelhar. 