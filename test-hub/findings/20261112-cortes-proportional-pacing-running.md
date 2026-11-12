# CORTES - regra proporcional universal para 23h (RUNNING)
STATUS: RUNNING
AREA: social-publishing / instagram / kwai / tiktok / linkedin / pinterest / pacing
DATE: 2026-11-12
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none
BASELINE_PROVEN: Confirmed Instagram posts via Graph/Neon; separate account-target quotas; current static 65s, 3min, 10min and 5min triggers are independent of the actual remaining daily inventory.
FAILED_AVOIDED: No real test posts; no replay of UNCERTAIN; no buffer queue reset; no touch of PC screen or input; no new paid provider.
SUCCESS_SIGNAL: Python math contracts all pass, JS Neon backend syntax passes; live enforcement only after audited deployment of exact backend and caller.
FAILURE_SIGNAL: Invalid timezone/first confirmation/limit causes a unit failure; parser failure; any publication before computed due time.
TEST_VALIDITY: Source-only unit tests and syntax; cannot claim production activation from a green unit job.
SCOPE: rules in tools/cortes_deadline_pacing.py, producer due validation and DB lease guard in infra/neon-cortes-queue/index.mjs.
