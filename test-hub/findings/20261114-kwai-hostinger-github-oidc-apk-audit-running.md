# Item 1 — autenticação OIDC GitHub para auditoria real dos APKs da Hostinger
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: GitHub-hosted proof-only OIDC lease
COMMIT: baseline d5f648217899ba4bfd370184006dda0f717e42a7
SUPERSEDES: none
OWNER: ChatGPT item1 PR #2616, files exclusivos tools/kwai_spawndroid_oidc_broker.php, tools/kwai_spawndroid_oidc_cloud_audit.py, .github/workflows/kwai-spawndroid-stage-cloud-audit.yml
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- Hostinger contém 25/25 APKs de com.kwai.video (202108730 bytes) com SHA256 local e remoto coerente; auditoria independente APK Signature Scheme v2 + digest de conteúdo de 25/25 retornou 0 erro no servidor.
- Hostinger fetch.php com HMAC existente e /signed/<expiry>/<signature>/<filename>.apk: GET/HEAD200 para assinatura válida, sha256_match=true, assinatura alterada 403, URL antiga preservada.
- Android SpawnDroid session anterior de demo + mobile:installMultipleApks retornou HTTP500. Novo canário path-only foi INVALID por CDP timeout e login /github.com/login, antes de criar qualquer sessão real. Sem novo teste Android ou login.
- GitHub Actions possui identidade OIDC por job via id-token:write e URL tokens.actions.githubusercontent.com JWKS HTTPS; Hostinger possui curl/OpenSSL/JSON no PHP. Não existe SPAWNDROID_API_KEY no GitHub secret inventory, portanto registro automático direto está bloqueado.

## FAILED_AVOIDED
- Não transferir chave HMAC permanente ao GitHub, não publicar APKs em repositório nem copiar os bytes para o PC, não contornar o login SpawnDroid, não repetir canário Android com CDP sem autenticação, não consumir minutos Android, não alterar publicadores ou executar publish.
- OIDC restringir estritamente issuer, audience, repo, ref, workflow_ref, evento, runner github-hosted e assinatura criptográfica RS256 de chave JWKS oficial. Todo link temporário expira em até 30min.

## SUCCESS_SIGNAL
- Novo endpoint PHP Hostinger somente POST, valida JWT RS256 e claims e emite apenas para job autorizado manifesto com 25 URLs HMAC .apk temporárias; teste sem JWT retorna 403, GET 405, não imprime secretos.
- Workflow GitHub-hosted automático restrito à branch própria obtém OIDC, baixa os 25 APKs do staging privado em runner efêmero, verifica SHA256, pacote, versão e assinatura APK oficial v2/v3 com apksigner Android, emite 25/25 PASS. Limpeza em finally. Nenhuma execução Android nem upload SpawnDroid.
- Testes de sintaxe/negação/autorização com logs auditáveis, registro de evidência em novo finding append-only, lease encerrado.

## FAILURE_SIGNAL
- PHP JWKS não acessível ou OIDC claim divergente => 401/403/503 fail-closed; CI não alcança prova e segue PARTIAL; não abrir exposição de arquivos. Falha ao baixar qualquer APK ou validar assinatura aborta sem registrar.

## TEST_VALIDITY
- Prova de bytes e assinatura no runner, não de instalação no SpawnDroid. O arquivo de PHP é novo e só entra por URL própria; fetch.php e .htaccess originais permanecem.
- Verificar HTTPS, id_token workflow, exact ref; impedir logging de URL HMAC e token JWT. Não usar branch main, não ativar cloud_cutover.

## LEASE
- Área exclusiva 'kwai-spawndroid-apk-oidc-read': apenas endpoint próprio no staging, workflow e utilitário novos na branch exclusiva #2616. Último HEAD verificado d5f648217899ba4bfd370184006dda0f717e42a7; sem workflows ativos no mesmo escopo. Revalidar HEAD imediatamente antes de escrever; peer GitLab main verificado sem script equivalente. TTL 30 minutos; não disputar kwai-login/publish/device com agentes 01-07.
