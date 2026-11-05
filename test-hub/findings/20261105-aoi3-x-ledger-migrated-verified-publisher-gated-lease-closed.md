# AOI #3 — X ledger migration PROVEN; publisher remains gated
STATUS: PARTIAL
ITEMS: [3]
DATE_UTC: 2026-11-05T03:09:53.424Z
AREA: x-ledger-inventory/live-readback + x-neon-ledger/migration-variable
LEASE: CLOSED
SUPERSEDES: lease-20261105-aoi3-x-current-legacy-inventory.md; lease-20261105-aoi3-x-neon-migration-gate.md
OWNER: chatgpt-aoi3-20261105
PRODUCTION_POSTS: 0
COST: R$0

GitHub workflow inventory run 41959354196, job 127021749074, completed/success. This was a single real authenticated read-only call to each old Northflank /x/post-status with GitHub issue comment readback. 10 identities: #385, #386, #387, #497, #513, #516, #520, #521, #522 CONFIRMED with original exact URLs; #1002 NOT_FOUND with no comments and unchanged open issue since 2026-10-22.

Independent Neon public.anthares_x_submission_ledger readback: 9 confirmed and no started. Issue #1002 SHA e2dc272927c55a5308b590396dc152f8a15d0c1c1eef7b75781bd1fa2478a5b4 remains absent from Neon. Historical 2026-10-29 inventory 40913350160 yields identical status, and current run confirms no drift.

Authenticated GitHub configuration: prior ANTHARES_X_AUTOPUBLISH=1, workflow x-anthares-browser-cloud-publisher.yml disabled_manually; ANTHARES_X_NEON_LEDGER_VERIFIED variable absent. Changed ANTHARES_X_AUTOPUBLISH=0 first, readback 0; created ANTHARES_X_NEON_LEDGER_VERIFIED=1, readback 1; publisher workflow remains disabled_manually. No new posting, queue claims, Neon's SQL write, media fetch, or worker run.

**COMPLETE:** historical X ledger migration proof and configuration gate. **PENDING:** actual authenticated X browser/vault readiness, sanctioned remote publisher promotion and Forgejo executor proof. Current Northflank /x/health browser_ready=false; do not start publication or mark global #3 DONE without live proof.
