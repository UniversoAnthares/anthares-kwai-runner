# Test Hub lease — CORTES F1 cloud replication worker (24/10/2026)

Owner: chatgpt-cortes-cloud-f1-worker-20261024
Job: cortes-f1-cloud-replication-gate-20261024
Target: UniversoAnthares/anthares-clipper, branch feature/cortes-cloud-drive-replication-20261023, head 85e903c93f4cc85bace4e07cbb5f2e705fbd9792 at acquisition.
Scope: new tools/cortes_cloud_drive_worker.py and tests/test_cortes_cloud_drive_worker.py only.
Purpose: implement and validate an off-Windows fail-closed scheduler around existing guarded rclone two-replica code. Never change publishers, base branch, service accounts, OAuth, actual media, or production schedules. Preconditions F1 OAuth dedicated are known blocked on Windows. No bypass.
GitLab peer: feature branch absent (404), no peer edits.
Duration: this task session only; release when finding is appended.
No production promotion or secrets.
