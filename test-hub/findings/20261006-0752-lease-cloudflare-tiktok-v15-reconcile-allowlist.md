# Lease — allowlist TikTok V15 reconcile workflow
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37458261489
JOB: none
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: Cloudflare OIDC/session-state works for allowlisted workflows; TikTok inventory isolation 30-way and earlier central-session probes are PROVEN.
FAILED_AVOIDED: run 37458261489 failed 30/30 at /tiktok/session-state HTTP 401 before inventory. Current Worker allowlist omits tiktok-v15-reconcile-30.yml, so rerunning unchanged is forbidden.
SUCCESS_SIGNAL: deployed Worker accepts OIDC from tiktok-v15-reconcile-30.yml and a 30-way read-only reconcile matrix crosses /tiktok/session-state.
FAILURE_SIGNAL: post-deploy 30-way matrix still receives 401 with verified deployed source.
TEST_VALIDITY: health/version and source allowlist must be verified after deploy; otherwise run is INVALID.
EXPIRES: 2026-10-06T08:22:00-04:00
