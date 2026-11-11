# Pinterest Buffer — auditoria produtiva e janela real de publicação
STATUS: PARTIAL / LEASE CLOSED
DATE_UTC: 2026-11-11
AREA: pinterest-buffer-production-readback
OWNER: chatgpt-cortes-item5-readback-20261111
SUPERSEDES: test-hub/findings/lease-pinterest-operational-readback-no-tests-20261111.md
MAIN_BASE_AT_CLOSURE: d5c2157121f24a486a7cd233383b5246c9424193
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1

## Alteração e fatos
- PR #2347 merge d5c2157121f24a486a7cd233383b5246c9424193: manual readback/audit/terminal-only workflows skip pre-existing synthetic test steps. Routine scheduler and production identity guards retained; publisher job no longer runs on a mere push to main.
- GitHub Actions https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43016395001 SUCCESS: operational `reconcile_only` run authenticated with Buffer and Neon OIDC; both test steps skipped, summary `RECONCILE_ONLY posts_confirmed_this_run=0 new_posts=0`.
- GitHub Actions https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43016477089 SUCCESS: authenticated `audit_pending_only` no mutation, 2 exact Buffer receipts verified for pinned Pinterest channel, both `scheduled` and `schedulingType=automatic`, no public links.
- Existing posts due exactly 2026-11-11T14:24:00Z (10:24 Campo Grande) and 2026-11-11T15:40:00Z (11:40 Campo Grande); no publish proof can precede those provider due times.
- Schedule continues on weekdays at UTC hour 13-23 minute 08 and next-day UTC 00-02 minute 08; after second due date, first eligible scheduled verification 2026-11-11T16:08:00Z (12:08 local), subject to GitHub Actions scheduling delays. No additional automation or second writer created.
- In parallel, actual LinkedIn readback https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43015689360 SUCCESS: one new official confirmation with `new_posts=0`; Neon `linkedin:primary` increased to 39 confirmed, remains 2 older uncertain without remote IDs.
- Other historical unresolved: Instagram 7, Kwai lucasrosalem 18 and universoanthares 1, Pinterest 9 (7 without remote, 2 due), LinkedIn primary 2. No one of these may be marked published or permanently failed without original external evidence.

## Closure scope
Readback/operational access and due-date determination PROVEN; item 5 overall remains PARTIAL until all unresolved records have independently verifiable outcomes. Retained 0 additional tests, 0 media re-posts, 0 new cloud services, 0 local media, 0 admin Neon SQL mutations.
CLOSED_LEASE: true
