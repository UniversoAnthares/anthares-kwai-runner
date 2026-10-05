# TikTok reidratação pelo segredo privado
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-1943-tiktok-central-restore-403.md

BASELINE_PROVEN: Render a91b7baf está LIVE; histórico mostra /session-test 200 em sessões anteriores; central GET atual retorna 403.
FAILED_AVOIDED: não depende do GET central para bootstrap; usa TIKTOK_STORAGE_STATE secret já previsto no workflow privado; não publica; identidade é validada antes de persistir.
SUCCESS_SIGNAL: CENTRAL_SESSION_LOAD=FALLBACK_SECRET + RENDER_OIDC_BOOTSTRAP=OK + RENDER_SESSION_TEST=OK identity_verified=true; persistência central é avaliada separadamente.
FAILURE_SIGNAL: secret ausente/inválido, bootstrap rejeitado, session-test rejeita identidade, ou Actions não inicia.
TEST_VALIDITY: falha de billing/runner é harness INVALID; falha de persistência central após identidade não invalida bootstrap/identidade comprovados.

## Objetivo
Reidratar o Render sem depender da leitura Cloudflare bloqueada e recuperar uma sessão TikTok validada.
