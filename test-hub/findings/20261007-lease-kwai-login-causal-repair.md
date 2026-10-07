# Lease — Kwai login surface probe causal repair + credentialed E2E
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-07
LEASE_AREA: kwai-login
LEASE_OWNER: cline-kwai-login-causal-repair
LEASE_EXPIRES: 2026-10-07T04:30:00Z
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: 20261007-lease-kwai-login-surface-discovery.md

BASELINE_PROVEN: run 37529160444 reached KWAI_LOGIN_UI_OPENED with a live tunnel and validated vault install; discovery probe run 37563219355 exercised the emulator path end to end.
FAILED_AVOIDED: probe 37563219355 INVALID (dump path mismatch, never read a UI tree) per 20261006-2252 — not a negative result; credentialed autologin must not run before the preparation gate is settled per 20261006-2241; no deep-link guessing, no coordinate spray, no challenge bypass, no PC/MEmu local, no official Kwai API.
SUCCESS_SIGNAL: (1) probe re-run with TEST_VALIDITY=OK logs a real UI tree containing at least one login-like clickable node or editable field; (2) interactive run passes preparation gate and reports KWAI_LOGIN_CONFIRMED with session state saved, or owner completes login through the tokenized URL within the window.
FAILURE_SIGNAL: probe again yields empty trees after the path repair, or the preparation gate cannot be settled within bounded waits after its causal repair.
TEST_VALIDITY: disposable cloud Android; probe phase uses no credentials; no publication; secrets never enter logs or findings.

## Objetivo
Reparar causalmente o probe de superfície (caminho de dump) e o gate de preparação do Kwai, então avançar o login autenticado até READY para o canário serializado.

## Consequência
Próximos agentos: observar este lease antes de mutar kwai-login. Ao encerrar, anexar finding com run/job/commit e a linha decisiva do log.
