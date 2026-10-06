# Lease: Kwai final login and production E2E
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-06T11:47:00Z
BASELINE_PROVEN: remote Android/Kwai reaches FSM_MAIN and the real login chooser deterministically; READY gate, promotion gate, queue fencing, heartbeat, publisher lifecycle, UNCERTAIN reconciliation and confirmation ledger are PROVEN.
FAILED_AVOIDED: do not repeat bare ikwai://login, non-exported Activities, fixed-coordinate Phone taps, or treat Chrome first-run as Studio failure. Current path uses the proven chooser plus the credentialed autologin acceptance and official Studio fallback diagnostics.
SUCCESS_SIGNAL: authenticated expected-account READY proof followed by exactly one canonical Kwai publication, independent verification, remote_id/evidence and central confirmed ledger.
FAILURE_SIGNAL: supported credential flow reaches OTP/challenge that cannot be completed non-interactively, or authenticated state cannot be established; then implement a new persistent cloud session/bootstrap mechanism rather than reverting to PC runtime.
TEST_VALIDITY: disposable cloud Android, validated vault, real chooser, credentials sourced only from GitHub secrets, no secret logging, READY required before publisher.

Objective: close the only remaining Kwai acceptance gate without PC runtime dependency.