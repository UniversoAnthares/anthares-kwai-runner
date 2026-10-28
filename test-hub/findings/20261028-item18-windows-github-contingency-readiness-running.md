# Item fixo 18 — Windows/GitHub: readiness e fencing do takeover
STATUS: RUNNING
AREA: architecture/windows-github-publication-contingency
DATE: 2026-10-28
RUN: one nonpublishing contract check only
JOB: not yet triggered
COMMIT: 23770c5ac3678b45a52d9745b2993cf805adc007
SUPERSEDES: none
LEASE: scoped to the two Windows fallback workflows and item18 evidence; no social publication or Windows file work.

BASELINE_PROVEN: Hostinger Forgejo Git independent mirror run 40746611827 and scoped CI/QA; GH canonical. Windows self-hosted runner installation has historical success but latest ARA command timed out and WinRemote shell was locked by another task. Canonical hosted GitHub publisher paths and both manual Windows last-resort files exist.
LIVE_NEON_READBACK_20261028: universo 414 confirmed / 88 queued / 10 uncertain with started but no remote ID; lucas4 115 confirmed / 199 queued / 2 closed_unverified with started but no remote ID. Cutover control for lucas4 shows cloud_enabled=true and a historical local freeze, not a fresh authorized takeover.
FAILED_AVOIDED: workflow_run=failure is NOT proof NOT_APPLIED; automatic Windows fallback may duplicate a remote upload. No worker activation, no execution of Windows browser/install, no release of uncertain ledger, no publication, no enabling disabled workflow, no forced ref writes.
SUCCESS_SIGNAL: both fallback source workflows cease auto dispatch on hosted workflow failure; future manual admission requires an explicit account-scoped approval flag and explicit publish opt-in, with default diagnostic_only=true; a single isolated static/CI test reports both guards PASS. Readiness contract declares TAKEOVER_ALLOWED=false until freeze, source terminal, remote reconciliation, generation fence, account identity and authorized live recovery all actually pass.
FAILURE_SIGNAL: any route can post automatically on upstream failure, any unconditional Windows job, or a test can publish/alter Neon.
TEST_VALIDITY: static source guard validation only; actual publication takeover remains UNPROVEN until independently authorized and reconciled. Do not mark item18 DONE from this test.
