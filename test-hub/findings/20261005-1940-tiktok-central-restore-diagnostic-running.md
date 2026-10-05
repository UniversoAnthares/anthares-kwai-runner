# TikTok central restore diagnóstico seguro
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: 914e4dc0fcf0410a73357c5eb21048fc4d67b615
SUPERSEDES: test-hub/findings/20261005-1937-tiktok-central-restore-valid-failure.md

BASELINE_PROVEN: revisão exata f9ed83d7 foi alcançada e restore retornou false; OIDC Render funcionou.
FAILED_AVOIDED: não repetir booleano opaco; Render a91b7baf retorna somente central_restore_http e central_restore_reason, sem state/cookies/token.
SUCCESS_SIGNAL: restored/200 e bootstrapped=true; se não, razão causal segura explícita.
FAILURE_SIGNAL: state_absent/404, control_http_error/401|403, state_payload_invalid/200 ou erro de transporte explícito.
TEST_VALIDITY: revisão deve ser a91b7baf; publisher permanece skipped.

## Objetivo
Determinar a causa exata do restore=false sem expor material de sessão.
