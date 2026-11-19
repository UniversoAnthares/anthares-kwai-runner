# Lease CORTES social preflight 19/11/2026

AREA: instagram-direct-ci + linkedin-company-ci (CI only, no queue mutation).
OWNER: ChatGPT current task. BASELINE_PROVEN: Instagram workflow run 44451351735 fails two clock-dependent unit tests; LinkedIn run 44449253132 fails on missing cryptography package. Branch baseline: 09b56b60f957bd5d8e4db4e5392b768981dbd8d5.
FAILED_AVOIDED: no publications, no social queue writes, no token changes; no overlap with tiktok-publish/kwai-publish/queue leases.
SUCCESS_SIGNAL: Python tests pass in CI; direct workflows proceed past the previous broken preflight.
FAILURE_SIGNAL: GitHub CI fails, protected branch rejects integration, or HEAD/peer diverges.
TEST_VALIDITY: same GitHub main baseline; no causally relevant active run; GitLab duo-main lacked both targets as of inspection, is stale, and must not be mirrored blindly.
STARTED_UTC: 2026-11-19T03:59:09.473Z
EXPIRES_UTC: 2026-11-19T04:28:09.473Z
STATE: RUNNING (branch only until integrated).
