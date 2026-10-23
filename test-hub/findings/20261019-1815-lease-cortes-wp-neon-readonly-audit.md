# Audit of CORTES WordPress vs Neon publication evidence
STATUS: RUNNING
AREA: kwai-publish, wp-neon-reconciliation
DATE: 2026-10-19
LEASE_OWNER: chatgpt-ci-audit-20261019
LEASE_EXPIRES_UTC: 2026-10-19T20:00:00Z
BASELINE_PROVEN: GH Clipper daily run 39299799396 green, but its dispatcher logged idle=awaiting_publication; GH run 39255821682 audited WP (39 stored / 36 pending / 3 completed) and enqueued one task. Neon production DB public.cortes_publications read-only query shows 39 kwai:lucasrosalem rows marked confirmed, but only four have public Kwai link; evidence kinds include 30 profile-account-new-post-time, and real publisher callback guard requires verifiable URL. Active Windows queue consumer reported QUEUE_EMPTY at 2026-10-19 14:09 local; WordPress callback pending file empty. The old source38 media is retained.
FAILED_AVOIDED: never infer actual posts from Neon confirmed status alone; do not retry uncertain/possibly published cuts; do not perform another Kwai publish as a diagnostic; do not reset queue, rewrite WordPress statuses, or modify existing video assets. No Android reboot.
SCOPE: read-only fresh WP authoritative counts from isolated GH Action (credentials retained inside secrets), compare aggregate with Neon, inspect proof/receipt taxonomy, propose minimal guard with test evidence. No WordPress GitHub→GitLab mirror mutation, no ARA executor changes. Existing consumer authority preserved.
SUCCESS_SIGNAL: fresh sanitized WP snapshot with stored/processing/completed counts and no tokens; explicit reconciliation report with proof-strength histogram; harmless isolated CI workflow completes.
FAILURE_SIGNAL: API auth denied, missing selfhosted runner, unverifiable state, or risk of duplicate publication. Mark PARTIAL and stop without mutation.
TEST_VALIDITY: no actual publication; tests are read-only and must not be represented as user-openable Kwai posts.
