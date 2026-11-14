# Item 1 — canário de instalação real SpawnDroid preparado no GitHub (sem credencial)
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43643867062
JOB: cloud-canary-offline-contracts 132597248092; original-apk-audit 132597248394
COMMIT: 43a43b68df73910f916f8ad3432e873c9113e825
SUPERSEDES: 20261114-kwai-cloud-appium-one-shot-api-canary-running.md
OWNER: ChatGPT item1 PR #2616
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## Avanço implementado
- Adicionado `tools/kwai_spawndroid_cloud_install_canary.py`, uma rotina one-shot GitHub-hosted que requer GITHUB_ACTIONS, repo e ref exatos, `workflow_dispatch`, `SPAWNDROID_API_KEY` de escopo autorizado, `SPAWNDROID_HOBBY_FREE_CONFIRMED=1`, `SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED=1` e slug DEMO exclusivamente `spawndroid-demo-ae64feef92`.
- Preflight autenticado lê GET /api/apps e GET /api/sessions; aborta em app.demo ausente, sessão ativa ou estado incerto. Somente com esses gates obtém manifesto OIDC e URLs HMAC de 1500s em Hostinger.
- Downloads em TemporaryDirectory do GitHub runner, 25 APKs auditados via SHA256, pacote, versão e Android apksigner originais; versão `com.kwai.video:647103`, volume `202108730`.
- Criação única via POST /api/v1/sessions com `Idempotency-Key: kwai-item1-<GITHUB_RUN_ID>-<RUN_ATTEMPT>`; resposta ambígua falha fechada e exige reconciliação. Runner Android 14 usa o app.demo existente apenas para boot, sem publicar.
- W3C WebDriver anexa à URL de sessão da API, executa `mobile: installMultipleApks` com 25 URLs path-only terminadas em .apk, verifica `isAppInstalled`, `listApps`, `activateApp`, `queryAppState`. Não acessa login nem editor de vídeos.
- try/finally sempre tenta DELETE WebDriver e DELETE /api/v1/sessions com resultado passed/failed, seguido de GET /api/sessions para readback. Falha no teardown bloqueia sucesso.
- `.github/workflows/kwai-spawndroid-stage-cloud-audit.yml` agora possui workflow_dispatch com consentimento explícito de canário, confirmação de plano Hobby gratuito e slug demo; job Android com timeout 11min e serialização `kwai-spawndroid-experimental`, compartilhada com o Stable Hub já no main. Default skip em push/PR, mantendo cutover OFF.
- Broker Hostinger `oidc-broker.php` atualizado na rota própria para autorizar apenas `push` ou `workflow_dispatch` do mesmo repo/ref/workflow e demais claims assinados por GitHub RS256; nenhuma chave HMAC foi exportada. Endpoint testado: GET sem token HTTP405, POST sem token HTTP403, POST inválido HTTP403.
- Código e testes no PR draft #2616; não alterados os publicadores atuais nem arquivos do Agente01/02.

## Evidência decisiva
- Run 43643867062:
  - Job 132597248092 `cloud-canary-offline-contracts=success`. `Ran 17 tests in 0.006s; OK`.
  - `SPAWNDROID_CANARY_KEY_GUARD=PASS`.
  - `SPAWNDROID_TEARDOWN_RECONCILE_REQUIRED_SYNTHETIC=PASS`.
  - `KWAI_SPAWNDROID_CLOUD_CANARY_NO_CUTOVER=PASS`.
  - Job 132597248394 `original-apk-audit=success`, `Ran 9 tests; OK`, `Ran 19 tests; OK`, `KWAI_CLOUD_ORIGINAL_25_APKS_SHA256_AND_APKSIGNER=PASS`.
  - Job `cloud-install-one-shot=skipped` corretamente: push de revisão sem workflow_dispatch e sem autorização manual.
  - `KWAI_PUBLICATION_ATTEMPTED=0`, sem sessão Android real desta rodada.
- PR HEAD registrado 43a43b68df73910f916f8ad3432e873c9113e825; `cloud_cutover.enabled=false` confirmado por main e na CI.
- Roteador de API precisa de credencial nova: consulta somente de nomes de secrets no GitHub revela ausência de `SPAWNDROID_API_KEY` e `SPAWNDROID_CI_TOKEN`. Browser isolado CDP continua em `github.com/login`; autenticação não foi contornada.

## Limites / próximos passos
- PROVEN: download original + assinatura (25 de 25), cliente OIDC/broker e regressão offline.
- PARTIAL: preparação e homologação do canário, sem sessão real. `workflow_dispatch` poderá exigir que o workflow esteja presente na branch default após revisão/merge; não afirmar execução manual imediata a partir de PR draft se o GitHub exigir default.
- BLOCKED: criar no próprio SpawnDroid uma API key legítima com scope `upload` (ou token CI do hub), guardá-la como GitHub secret e confirmar em dashboard Hobby minutes/slot antes do disparo manual. SSO no perfil isolado expirou.
- Quando API autorizada estiver disponível: disparar um único canário após TestHub/device lease, observar W3C RESULT, provar pacote e launcher, terminar e reconciliar. Não promover publicador, nem criar sessões adicionais caso POST retorne incerto.
- Um APK universal legítimo para POST /api/apps não foi obtido; a estratégia de splits usa o demo artifact como portador e não gera `app.slug` próprio.
- Cleanup: TemporaryDirectory ephemerally remove os arquivos; nenhuma escrita no PC e nenhum segredo público. Script não transmite JWT/URLs ao log.

## Lease closure
Encerrado desenvolvimento exclusivo `kwai-spawndroid-item1-cloud-canary` neste commit. Novos testes reais requerem lease independente e evidência de quota/autorização.
