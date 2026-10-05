# Probe central TikTok inválido por allowlist OIDC do Cloudflare
STATUS: PARTIAL
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37385518878
JOB: 112017706793
COMMIT: feee16aa44a35016fea5d54084a9f1cfbee483e7
SUPERSEDES: test-hub/findings/20261005-1855-tiktok-central-session-read-running.md

BASELINE_PROVEN: GitHub OIDC token issuance funcionou; endpoint anthares-control respondeu.
FAILED_AVOIDED: não classificar 401 como sessão ausente; não alterar cloudflare-control pelo CHAT 3.
SUCCESS_SIGNAL: CENTRAL_SESSION_AVAILABLE.
FAILURE_SIGNAL: CENTRAL_SESSION_ABSENT somente com OIDC autorizado.
TEST_VALIDITY: 401/403 é PROBE_AUTH_INVALID e não testa persistência.

## Objetivo
Determinar se o estado TikTok existe no controlador sem mutação.

## Resultado
Harness inválido para a hipótese. O token OIDC foi obtido, mas GET /tiktok/session-state respondeu HTTP 401 e o probe emitiu PROBE_AUTH_INVALID. Logo não há evidência de sessão presente nem ausente.

## Evidência decisiva
Job 112017706793: HTTP 401; PROBE_AUTH_INVALID. O contrato atual de cloudflare-worker/src/index.js usa allowlist de workflow e não inclui tiktok-central-session-read.yml.

## Consequência
CHAT 3 não deve modificar cloudflare-control. CHAT 4 precisa fornecer/autorizar contrato de leitura do estado central para workflow TikTok ou mecanismo equivalente. Até lá, investigar pelo domínio TikTok/Render sem repetir este probe e sem concluir CENTRAL_SESSION_ABSENT.
