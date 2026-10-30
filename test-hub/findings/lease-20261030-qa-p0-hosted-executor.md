# QA-P0 hosted diagnostics executor lease
STATUS: RUNNING
AREA: architecture/qa-p0
DATE: 2026-10-30
RUN: none
JOB: none
COMMIT: 88684f7950e99797ed399a8d3943e657c3d45688
SUPERSEDES: none

BASELINE_PROVEN: QA-P0 controller runs on GitHub-hosted Ubuntu (main run 40992225120 successful), executor remains Windows qa-p0-independent. Existing recovery script can wake a local Windows scheduled task in daily incident. Local Pinterest CDP audit depends on PC.
FAILED_AVOIDED: no local task wake from cloud, no media resend, no bypass 401/403 WordPress, no new publishing, no closure of P0 incidents. Retain strict P0 validation, dedupe and capacity protection.
SUCCESS_SIGNAL: Ubuntu policy test succeeds on PR; main workflow_dispatch of an existing authorized QA-P0 issue verifies diagnostic and readback; no PC runner.
FAILURE_SIGNAL: cloud code failing, unauthorized dispatch, local recovery silently treated as performed, wrong issue.
TEST_VALIDITY: PR regression check plus real main run; a diagnostic PASS never proves publication repair.
LEASE_SCOPE: .github/workflows/cortes-qa-p0-executor.yml and tools/cortes_qa_p0_recovery.ps1 only, with one append-only closing finding, expires 30 minutes. Source main and branch readback required before merge.
