# Lease TikTok session restore causal fix
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: test-hub/findings/20261005-1849-lease-tiktok-session-central-read.md

LEASE_AREA: tiktok-session
OWNER: CHAT-3
EXPIRES_AT: 2026-10-05T23:55:00Z
BASELINE_PROVEN: GitHub OIDC -> Render funciona; Render deploy cdd656b5 executa session-status; central read probe 37385518878 foi inválido por allowlist e não prova ausência de sessão.
FAILED_AVOIDED: não usar ANTHARES_CONTROL_TOKEN; não alterar cloudflare-control; não repetir workflow não allowlisted; corrigir NameError silencioso de urllib antes de novo restore.
SUCCESS_SIGNAL: Render restaura STATE por token Cloudflare OIDC efêmero vindo de workflow TikTok já autorizado e session-status retorna bootstrapped=true/central_restored=true.
FAILURE_SIGNAL: token Cloudflare OIDC autorizado chega ao Render e GET central retorna resposta conclusiva sem restaurar estado.
TEST_VALIDITY: separar 401/403 de sessão ausente; verificar revisão Render implantada; nenhuma rota de publicação será chamada.

## Objetivo
Corrigir a cadeia de restauração TikTok sem token estático e sem mudança no controlador Cloudflare.
