# TikTok Render env-seed fallback
STATUS: RUNNING
AREA: session
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: 9556b04e33f31e2f1c3ae9a94d074860881dc1d0
SUPERSEDES: test-hub/findings/20261005-1947-tiktok-private-actions-harness-invalid.md

BASELINE_PROVEN: central GET retorna 403; private Actions não executa steps; Render a91b7baf diagnosticou isso corretamente.
FAILED_AVOIDED: não usa private runner; não altera Cloudflare; após 403, Render 1917fb35 tenta apenas seed TIKTOK_STORAGE_STATE já configurado no próprio ambiente, sem expor valor.
SUCCESS_SIGNAL: central_restore_reason=restored_from_env_seed + bootstrapped=true, seguido de TIKTOK_SESSION_AND_IDENTITY_PROVEN.
FAILURE_SIGNAL: revisão correta e bootstrapped=false após fallback indica seed ausente/inutilizável no Render.
TEST_VALIDITY: publisher skipped; identidade só roda se estado restaurado.

## Objetivo
Recuperar sessão no próprio Render sem depender do GET Cloudflare nem do Actions privado.
