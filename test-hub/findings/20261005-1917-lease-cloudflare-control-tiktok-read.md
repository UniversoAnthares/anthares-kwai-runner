# Lease cloudflare-control: autorizar leitura central TikTok por OIDC
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: cloudflare-control
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: cloudflare-control
LEASE_EXPIRES: 2026-10-05T23:47:00Z

BASELINE_PROVEN: test-hub/findings/20261005-1811-tiktok-oidc-proven-session-lost.md — OIDC GitHub criptograficamente validado funciona; cloudflare-worker atual restringe workflow por allowlist.
FAILED_AVOIDED: test-hub/findings/20261005-1915-tiktok-central-read-oidc-not-allowed.md — não repetir probe com workflow fora da allowlist; test-hub/findings/20261005-2247-cloudflare-private-runner-failed.md — não repetir deploy pelo mesmo runner privado sem mudança causal.
SUCCESS_SIGNAL: workflow tiktok-central-session-read recebe resposta autenticada de /tiktok/session-state (200/404 sem 401); 404 significa auth válida e estado ausente, não falha de contrato.
FAILURE_SIGNAL: 401 com jwt_workflow após deploy confirmado da versão que inclui o workflow.
TEST_VALIDITY: somente vale contra Worker cuja versão/commit novo tenha sido efetivamente deployado; falha de runner/deploy é INVALID para a hipótese OIDC.

## Objetivo
Fechar a lacuna delegada ao CHAT 4: permitir leitura autenticada do estado central TikTok pelo workflow público sem afrouxar validações de issuer/audience/repository/ref/event/signature.

## Consequência
Nenhum outro agente deve mutar cloudflare-control durante este lease. Diagnósticos read-only permanecem permitidos.
