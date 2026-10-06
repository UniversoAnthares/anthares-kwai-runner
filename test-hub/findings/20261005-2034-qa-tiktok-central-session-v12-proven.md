# TikTok central session is available through production v12
STATUS: PROVEN
AREA: session
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394495580
JOB: 112047121732
COMMIT: 34efb93dafa3dfa9ede1d0729a9af900804e3776
SUPERSEDES: test-hub/findings/20261005-2029-running-tiktok-session-v12-read-probe.md

BASELINE_PROVEN: production Cloudflare v12 with GitHub OIDC allowlist.
FAILED_AVOIDED: pre-v12 403 restore path was not repeated against the stale Worker; production changed causally to v12.
SUCCESS_SIGNAL: HTTP 200, available=true, cookies list, CENTRAL_SESSION_AVAILABLE.
FAILURE_SIGNAL: 401/403 or available=false.
TEST_VALIDITY: read-only OIDC workflow, no publish and no session mutation.

## Resultado
SUCCESS_SIGNAL ocorreu. OIDC foi aceito pelo Worker v12 e o estado central TikTok existe: HTTP 200, available=true, cookie_count=21, updated_at=2026-10-05T17:30:39.301Z.

## Evidência decisiva
Job 112047121732 emitiu CENTRAL_SESSION_AVAILABLE com http=200 e 21 cookies.

## Consequência
O antigo blocker HTTP 403/central session absent está encerrado. CHAT 3 pode avançar para restore dessa sessão no Render e prova de identidade da conta, mantendo publicação bloqueada até ready_for_tiktok/identity_verified. Não criar nova sessão manual antes de testar o estado central já existente.