# AOI #08/#18 — ci quota Windows removido do main
STATUS: PARTIAL
LEASE: CLOSED
AREA: quota-ci-static
DATE_UTC: 2026-11-09
ITEMS: [8,18]
OWNER: chatgpt-aoi08-clipper-quota-ci-20261109
SUPERSEDES: lease-aoi08-clipper-quota-ci-no-windows-20261109.md
LEASE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2217
CODE_PR: https://github.com/UniversoAnthares/anthares-clipper/pull/243
CODE_MAIN_COMMIT: 818288b078792fcc8a6a72dac19c32ce68fd8ae1
CODE_WORKFLOW_SHA: 8c76a0dfdd2d10b2c580ed0601521ba50b4eb303
GOVERNANCE_VERSION: 223433740e807a90
READBACK: workflow main uses ubuntu-24.04 + setup-python 3.11, retains five unit test modules and all original unittest commands, no Windows path.
VALIDATION: source static checks 8/8 PASS and GitHub main readback; no hosted Actions job/real quota failover receipt verified.
PRODUCTION: no queue, publisher, session, cron, branch-protection or paid-plan changes.
CLOSURE: scoped code and lease changes merged; test-hub lease closed.
ACCEPTANCE: terminal criterion of item 8 remains PARTIAL pending verified terminal cancellation, independent quota handoff and receipt. Item 18 remains PARTIAL pending real fallback acceptance.
