# Claude GitHub protected-main lease repair: real API acceptance
STATUS: PARTIAL
AREA: claude-github-tools
DATE: 2026-10-20
SUPERSEDES: 20261020-claude-protected-main-lease-running.md
LEASE_STATE: CLOSED
BASELINE_PROVEN: b6093714914ff2c1e544e4cf867c04215ee8ac4b; GitHub/GitLab github-bridge.mjs blob c20bc84bc44ae37bb55a27cc7e243dbe0e126f62 equal.

Ruleset 25443611 requires PRs on main, with no bypass actors. The old begin-task PUT targeted main; the bridge erased upstream detail to generic HTTP 409. Existing Claude lease had expired on October 19. Do not remove main protection or assume another agent blocks the test.

Fix uses fixed test-hub/claude-github-leases ref for operational leases, initialized once from main without reset. Atomic GraphQL expectedHeadOid fences the complete lease scan; exact committed content is read back. Both legacy main and coordination leases remain checked. Main SHA is returned separately. Known branch-protection errors get a specific safe error code; arbitrary upstream bodies remain private. Read-only access to coordination markdown is permitted only on the hub, code writes cannot target this ref.

Validation: 36 local bridge/OAuth/security tests passed. Real patched-module calls using owner GitHub CLI credential (never printed) created lease test-hub/findings/lease-claude-github-20261020141800-0644079a.md, branch claude/lease-fix-acceptance-1792505876110, verified docs/claude-lease-fix-acceptance.txt commit 9f43b92b515db7b919f2b44380c093ff2a8a06a8 and draft PR https://github.com/UniversoAnthares/anthares-kwai-runner/pull/253. Source main remained b6093714914ff2c1e544e4cf867c04215ee8ac4b throughout the test. Disposable PR must not merge.

This proves patched code with actual protected GitHub, not a Claude UI invocation or production Worker deployment. Official guarded CI/deployment and real Claude caller acceptance remain separate.
