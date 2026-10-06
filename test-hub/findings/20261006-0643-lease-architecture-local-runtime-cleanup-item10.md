# Lease — architecture local runtime cleanup item 10
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
LEASE_EXPIRES: 2026-10-06T11:10:00Z
BASELINE_PROVEN: PC/local and Oracle are ABANDONED; production Cloudflare strategy routes only cloud executors; GitHub/CircleCI Android ADB is cloud execution and remains allowed.
FAILED_AVOIDED: do not delete cloud Android/ADB tooling merely because it uses adb; do not remove historical findings; do not replace proven cloud publishers with new untested paths.
SUCCESS_SIGNAL: operational runtime contains no self-hosted/Windows-PC executor, MEmu, Cookie Bridge, LOCAL_EXECUTOR, Windows scheduled task, C:/Users or D:/AntharesWork dependency; Cloudflare cannot select local/oracle/google even when injected; CI fails if these dependencies are reintroduced.
FAILURE_SIGNAL: any production route still requires a user-PC filesystem/process/browser or controller can select a retired executor.
TEST_VALIDITY: distinguish loopback internal to a cloud job/tunnel from dependency on the user's PC; classify only operational runtime, not tests/findings/history.

## Scope
Remove or neutralize only still-operational local-runtime residue. Preserve cloud Android ADB, isolated QA fixtures and append-only history.