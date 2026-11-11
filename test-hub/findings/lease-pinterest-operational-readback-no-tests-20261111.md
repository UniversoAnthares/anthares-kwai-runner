# Lease — reconciliação operacional Pinterest sem bateria de testes
STATUS: RUNNING
AREA: pinterest-buffer-production-readback
DATE_UTC: 2026-11-11
OWNER: chatgpt-cortes-item5-readback-20261111
BASE_MAIN: e391d4947918ea749c075e85125aff54c440b367
BASE_BLOB: b418add86aabfd9496b3e304e0909dd70b531348
BASELINE_PROVEN: Pinterest 9 uncertain, 2 Buffer remote IDs, 7 historic IDs missing; 2026-11-11 run 43005471890 read-only records SCHEDULED. All existing Pinterest workers completed; official cron must remain active.
FAILED_AVOIDED: user explicitly forbids additional testing; skip existing synthetic test steps on manual reconciliation. No new media posts, no manual Neon SQL, no local PC files or credentials, no blind resubmission.
SUCCESS_SIGNAL: main explicit reconcile_only=true performs operational authenticated Buffer readback; new_posts=0 and preflight unit steps skipped; confirmed URLs only where Buffer says sent; ledger CAS preserved.
FAILURE_SIGNAL: expected content moves, wrong provider identity, new post created by readback, another active lease, authorization or quota error.
TEST_VALIDITY: operational readback with real provider, no synthetic tests.
LEASE_STATUS: OPEN
