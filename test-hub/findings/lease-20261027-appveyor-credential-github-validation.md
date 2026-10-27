# Lease — AppVeyor credential validation
STATUS: RUNNING
AREA: CI quota / AppVeyor secrets
DATE: 2026-10-27
RUN: none
JOB: none
COMMIT: 5560f424ab73d5a8130fdd73bae597057b67259e
SUPERSEDES: none

Owner ChatGPT. Scope: verify newly saved APPVEYOR_API_TOKEN in GitHub Actions via project-scoped read-only API call. Use exact known UniversoAnthares/anthares-kwai-runner identities. No token output, no sample quota, no external build creation, no paid plans. No modifications to other watchers or publishers. Lease 30 min.
SUCCESS_SIGNAL: workflow run real AppVeyor API GET returns verified matching repository account and project; if API rejects log safe failure category only.
