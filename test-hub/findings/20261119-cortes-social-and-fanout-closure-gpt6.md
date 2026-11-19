# 19/11/2026 — CORTES cloud preflight and social fanout closure

Baseline and leases: 20261119-lease-cortes-social-preflight-gpt6.md, 20261119-lease-cortes-fanout-wordpress-transient.md and 20261119-lease-linkedin-admin-reason.md.

## Instagram direct CI: FIXED in main
- PR #2659 merged commit 717f0f3ab4f03aaed89ca23cc59ed59d609fffde.
- Real GitHub Actions run 44455474338 completed success with all relevant tests. It was outside the authorized 06:00 publication window; publication was not claimed.

## LinkedIn company: CI FIXED; provider authorization BLOCKED
- PR #2659 and QA run 44455373732 success fixed missing cryptography and outdated QA contract.
- PR #2661 merged commit 9230fe4902440f38fb5cde108fe19cbfaff33eff, QA run 44456386895 success.
- Real run 44456493014 reached the organization OAuth role preflight and failed closed with LINKEDIN_COMPANY_ADMIN_READ_AUTH_REQUIRED. Consenting member OAuth is present; dedicated organization OAuth is absent. Need legitimate role/scope authorization; no queue lease or post in this failing path.

## Three-network fanout: transient read recovery FIXED
- PR #2660 merged commit 5f96a9e1288139b9b1c7ec3e7baf26701790bb2c.
- GitHub Actions run 44456268776 success, seven offline regression tests passed, including one bounded transport-only retry and no retry on HTTP denial.
- Read-only WordPress diagnostic confirmed 104 eligible masters and new_enqueues=0. Ordinary future scheduled runs remain Neon-fenced.

## Safety and residual limits
- No queue rewinds, replay of UNCERTAIN media, token logging or manual publication took place in these patches.
- Leases closed here after verification; operational LinkedIn authorization remains pending independently.
- CORTES Shorts WordPress atomic claim and Pinterest runner availability remain distinct unresolved causes; do not infer publication success from a green CI run.

STATE: CLOSED / PARTIAL for LinkedIn external authorization.
