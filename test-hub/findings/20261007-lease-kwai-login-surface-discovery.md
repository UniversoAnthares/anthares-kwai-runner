# Lease — Kwai login surface discovery probe
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-07
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-07T03:30:00Z
BASELINE_PROVEN: remote Android/Kwai reaches FSM_MAIN deterministically; READY gate, promotion gate, queue fencing, heartbeat, publisher lifecycle, UNCERTAIN reconciliation and confirmation ledger are PROVEN.
FAILED_AVOIDED: do not repeat bare ikwai://login, non-exported Activities, fixed-coordinate Phone taps, or treat Chrome first-run as Studio failure. Do not repeat credentialed autologin until the non-credentialed probe exposes the real login entrypoint.
SUCCESS_SIGNAL: probe log contains at least one editable account/phone/email field or a clickable login control with stable resource-id/text before any credential is entered.
FAILURE_SIGNAL: probe completes with zero editable nodes and zero login-like clickable nodes in all phases; then implement a new persistent cloud session/bootstrap mechanism rather than reverting to PC runtime.
TEST_VALIDITY: disposable cloud Android, no credentials used, no secret logging, probe log saved to artifacts.

## Objetivo
Descobrir a superfície real de login do Kwai sem repetir autologin cego. Instrumentar a árvore UI após onboarding/Profile e registrar texto/resource-id/class/clickable/bounds por transição.

## Consequência
O próximo autologin E2E deve usar apenas rotas/controles expostos por este probe. Não repetir coordenadas cegas ou taps em nodes não-clickable.
