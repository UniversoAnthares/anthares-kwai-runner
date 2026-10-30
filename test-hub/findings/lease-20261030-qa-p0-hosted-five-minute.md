# QA P0 hosted five-minute parity lease
STATUS: RUNNING
AREA: architecture/qa-p0
DATE: 2026-10-30
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41055843075
JOB: 124063037794
COMMIT: 70ae59d4792c2d462641085dd050e3da2b584967
SUPERSEDES: none

BASELINE_PROVEN: Hosted watchdog source scan on Ubuntu succeeded, WordPress state read 0 failures, QA router observations=2, opened=0, sources_failed=0. Hosted fallback alert also succeeded. WinRemote TaskList queried exact old Anthares CORTES P0 QA Immediate Independent, P0, QA and Anthares: old task absent, distinct Pinterest task present.
FAILED_AVOIDED: Do not disable any other scheduled Windows task, do not alter publishers or P0 incident effects; preserve existing cloud-alert twice-hourly cadence, old route concurrency lock.
SUCCESS_SIGNAL: Main workflow hosted QA route succeeds after adding five-minute cron; old 13,43 clock remains dedicated to cloud-alert, no unexpected duplicate scan.
FAILURE_SIGNAL: both jobs run on same schedule, missed auth, CI quota exceeded or duplicate incidents.
TEST_VALIDITY: Verify readback and real hosted main push run, scheduled run separately if available.
LEASE_SCOPE: .github/workflows/cortes-qa-p0-publication-watchdog.yml, 30 minutes.
