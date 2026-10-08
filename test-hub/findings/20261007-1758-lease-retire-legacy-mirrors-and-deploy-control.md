# Lease retire legacy mirrors and deploy control
STATUS: RUNNING
AREA: architecture/cloudflare-control
DATE: 2026-10-07
BASELINE_PROVEN: Anthares Git Mirror is the sole intended synchronizer; anthares-control provider router is reconciled in GitHub/GitLab.
FAILED_AVOIDED: no bidirectional native mirror, no Actions/CI mirror secrets, no force-push, no write on SHA divergence.
SUCCESS_SIGNAL: legacy gitlab-mirror-sync workflows absent from all eight repos; reconciled Worker deployed; production provider self-test passes all five fail-closed cases.
FAILURE_SIGNAL: competing mirror remains, deploy differs from reconciled source, or any failover case permits divergent write.
TEST_VALIDITY: verify files directly on providers and query deployed Worker endpoint after deployment.
LEASE: expires in 30 minutes.
