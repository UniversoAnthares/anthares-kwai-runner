# AOI #3 — X Neon migration proof gate
STATUS: RUNNING
AREA: x-neon-ledger/migration-variable
OWNER: chatgpt-aoi3-20261105
DATE_UTC: 2026-11-05T03:07:36.667Z
EXPIRES_UTC: 2026-11-05T03:37:36.667Z
BASE_MAIN: 640676473cc03bd638640cfcc1680857f3e3c47c
ITEMS: [3]
GOVERNANCE_SHA: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
BASELINE_PROVEN: GitHub read-only inventory run 41959354196 completed/success; 10 exact source legacy hashes, 9 CONFIRMED, #1002 NOT_FOUND with zero issue comments/unchanged since 2026-10-22. Neon 9 confirmed, no other records. GitHub cloud X workflow disabled_manually. ANTHARES_X_NEON_LEDGER_VERIFIED variable 404; ANTHARES_X_AUTOPUBLISH=1 but workflow disabled. X Northflank browser_ready=false.
SCOPE: set AUTOPUBLISH=0 before independent migration verified flag=1; leave X publisher workflow disabled_manually; no new X post, no claim, no external worker, no GitLab/Forgejo admin changes.
SUCCESS_SIGNAL: both variables read back 0 and 1, workflow stays disabled; existing hashes exact. Post lease closure finding.
FAIL_SIGNAL: variable write denied, workflow unexpectedly active or issue changed, then abort safely.
TEST_VALIDITY: current authenticated old ledger proof, read-only Neon and GitHub variable state.
