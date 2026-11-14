# Item 1 — implantação de canário Android real a partir do GitHub cloud (sem PC)
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: aguardando prova CI de contratos offline
JOB: ChatGPT item1 / PR #2616, branch exclusiva
COMMIT: baseline b64538751b91965fa86c43106f33e483b67aa856
SUPERSEDES: none
OWNER: ChatGPT item1 cloud-appium-canary
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- 25 APKs de `com.kwai.video` versão 647103, 202108730 bytes, SHA256 e apksigner oficial comprovados no GitHub Actions run 43641732854 com OIDC + HMAC da Hostinger. Broker `oidc-broker.php` aceita somente push no workflow da branch PR #2616.
- Browser SpawnDroid isolado CDP 29241 atualmente `github.com/login`; sessão pessoal protegida, nenhum bypass autorizado.
- Repositório GitHub não apresenta `SPAWNDROID_API_KEY` nem `SPAWNDROID_CI_TOKEN` nos nomes de secrets. Não iniciar sessão real sem credencial legitimamente criada.
- Teste Android anterior com URLs query deu HTTP 500; novo path-only instalador não foi testado pois CDP falhou antes de iniciar sessão, status INVALID.
- SpawnDroid documentação: POST /api/v1/sessions com `artifactId` cadastrado, `Idempotency-Key`; WebDriver em `webdriverUrl`; GET readiness e DELETE com resultado explícito. Driver UiAutomator2 permite `mobile: installMultipleApks`; Hobby 200 minutos/mês, 1 slot, 15 min/sessão, 3 min idle.
- Production `cloud_cutover.enabled=false`, publicadores existentes preservados; não iniciar publicação/login Kwai.

## FAILED_AVOIDED
- Não refazer download de APK externo 403, reempacotar ou resignar.
- Não usar mouse/teclado/cookies/senhas pessoais, nem escrever arquivos no PC.
- Não tentar canário sem SPAWNDROID_API_KEY com escopo autorizado + indicação explícita de cota Hobby + demo app.slug existente + slot disponível.
- Não repetir instalação com URLs query. Appium receberá URLs path-only .apk de 25 arquivos reais já auditados no runner cloud.
- Não fazer login nem publicar vídeo. Qualquer erro após solicitação de sessão exige readback idempotente; não reprovisionar outra sessão automaticamente.

## SUCCESS_SIGNAL
- Criar `tools/kwai_spawndroid_cloud_install_canary.py` e testes offline sem efeitos; workflow manual gated por inputs, secret, `cloud_cutover=false`, `id-token:write`, concurrency serializada e timeout curto.
- Atualizar somente broker e client OIDC da PR para permitir `workflow_dispatch` explicitamente no mesmo workflow/ref, preservando allowlist estrita e assinatura JWT.
- Testes sintéticos comprovam: ausência de key/cota aborta ANTES de OIDC ou POST; sessão existente bloqueia; Idempotency-Key fixa; W3C e teardown em finally, inclusive erro HTTP 500; nenhum publish; recibo instalado e pacote versão corretos.
- CI offline verde em runner hospedado, documentação e finding PARTIAL; o canário real permanece bloqueado até chave oficial e autorização do titular.

## FAILURE_SIGNAL
- Testes CI falham, mudanças concorrentes no HEAD, broker OIDC passa a permitir outro repo/ref, fluxo tenta criar sessão sem token, não encerra sessão em erro, vazamento de URL/token, consumo de minutos sem gate.
- Se plano exigir pagamento ou acesso for 401/403, abortar e declarar bloqueio.

## TEST_VALIDITY
- OFFLINE contratos não demonstram Appium no SpawnDroid. O canário real só se torna PROVEN com sessão `ready`, pacote instalado/versão, `mobile: activateApp` e `queryAppState`, teardown confirmado e relatório de quota sem cobrança.
- Registrar PASS de 25 APKs é prova de bytes assinados, não instalação.

## LEASE
Escopo próprio `kwai-spawndroid-item1-cloud-canary`: novo script e teste, extensão do workflow existente e do broker OIDC de propriedade da PR #2616, 30 minutos. Peer GitLab main lido sem novos arquivos. O lease se aplica somente ao desenvolvimento; o uso real de dispositivo exige lease adicional com quota/slot no momento da execução.
