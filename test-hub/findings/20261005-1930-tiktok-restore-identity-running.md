# TikTok restore + identidade via OIDC delegado
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: 8f0afbc37ae4bbed0b85499993bcf6271777b32b
SUPERSEDES: test-hub/findings/20261005-1915-tiktok-central-read-oidc-not-allowed.md

BASELINE_PROVEN: GitHub OIDC -> Render é PROVEN; tiktok-real-publish.yml pertence à allowlist conhecida do Cloudflare; Render deploy fc26d51a foi disparado.
FAILED_AVOIDED: usa workflow Cloudflare-allowlisted; corrige import urllib.request; usa token OIDC efêmero de audiência Cloudflare passado por header, não token estático; não chama publisher.
SUCCESS_SIGNAL: revisão Render fc26d51a ativa + SESSION_RESTORE_SAFE bootstrapped=true central_restored=true + TIKTOK_SESSION_AND_IDENTITY_PROVEN.
FAILURE_SIGNAL: revisão correta ativa e restore autorizado retorna ausência/erro conclusivo, ou session-test rejeita a identidade.
TEST_VALIDITY: 401/403, revisão errada ou falha de harness não contam como sessão/identidade FAILED; resposta de session-test é filtrada para nunca imprimir refreshed_state/cookies.

## Objetivo
Provar restauração central e, somente se ela funcionar, validar a conta TikTok exata sem publicar vídeo.
