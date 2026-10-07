# Lease — Kwai login clear-data surface force
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-07
LEASE_AREA: kwai-login
LEASE_OWNER: grok-kwai-login-clear-data
LEASE_EXPIRES: 2026-10-07T15:10:00Z
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: 20261007-lease-kwai-login-causal-repair.md

BASELINE_PROVEN: run 37417286394 reached LOGIN_SURFACE_REACHED (Welcome to Kwai / phone / Google / Facebook) after FSM_MAIN; vault install + API35 emulator PROVEN; surface discovery runs today (37609057022, 37613550316) proved cached authenticated MAIN / PWA with zero editable nodes.
FAILED_AVOIDED: bare ikwai://login; non-exported Activities; coordinate spray; credentialed autologin before login surface; treating PWA-no-native as permanent negative without causal change; expired leases 20261007-lease-kwai-login-*.
SUCCESS_SIGNAL: after pm clear + relaunch, probe log shows editable field OR login-like clickable (Log in / phone / email / sign in) with TEST_VALIDITY=OK and LOGIN_SURFACE_FORCED=1.
FAILURE_SIGNAL: after clear-data, still zero editable and zero login-like nodes across bounded snapshots while TEST_VALIDITY=OK.
TEST_VALIDITY: disposable cloud Android; no credentials; no publication; secrets never logged; empty-tree = INVALID not FAILED.

## Objetivo
Causal repair: sessão cached no feed bloqueia a superfície de login já comprovada. Forçar `pm clear com.kwai.video` após install e reabrir o app para reexpor a UI de autenticação.

## Consequência
Outros agentes: não mutar kwai-login até este lease expirar ou ser supersedido. Após o run, append finding com evidência decisiva.
