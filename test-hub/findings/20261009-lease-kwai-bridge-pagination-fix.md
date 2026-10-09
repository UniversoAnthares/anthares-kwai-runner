# Lease bridge pagination fix
STATUS: RUNNING
AREA: kwai-bridge-pagination
DATE: 2026-10-09
OWNER: chatgpt-bridge-pagination-fix
LEASE_UNTIL: 2026-10-09T18:45:00Z
BASELINE_PROVEN: issue comments API ignores descending sort; page 2 has pending commands.
FAILED_AVOIDED: first-page-only polling.
SUCCESS_SIGNAL: newest command processed by live bridge.
FAILURE_SIGNAL: missing response.
TEST_VALIDITY: CI alone does not prove live bridge.
