# Lease renewal — architecture local runtime cleanup item 10
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
SUPERSEDES: test-hub/findings/20261006-0643-lease-architecture-local-runtime-cleanup-item10.md
LEASE_EXPIRES: 2026-10-06T11:45:00Z
BASELINE_PROVEN: main contains cloud-only runtime guard and production publisher rename in commit 68cc5211897701747d0abfb6a52b9320eec9fc81; local static test reports CLOUD_ONLY_RUNTIME=PROVEN; operational grep returned no MEmu, LOCAL_EXECUTOR_*, Cookie Bridge, C:/Users, D:/AntharesWork, self-hosted/Windows runner, schtasks, or tiktok_web_publish_local references.
FAILED_AVOIDED: cloud Android ADB and intra-job 127.0.0.1 tunnels are valid cloud execution and must not be removed; append-only history/tests are not production dependencies.
SUCCESS_SIGNAL: GitHub-hosted postdeploy safety workflow asserts the deployed routing revision, pc_fallback=false, no retired route, all failover checks true, and cloud-only static scan succeeds from a fresh checkout.
FAILURE_SIGNAL: fresh GitHub checkout finds a PC/local runtime dependency or deployed controller exposes/selects a retired executor.
TEST_VALIDITY: workflow must run on ubuntu GitHub-hosted runner; no self-hosted runner or user-PC filesystem may participate.