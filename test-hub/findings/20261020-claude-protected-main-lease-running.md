# Claude GitHub protected-main lease repair
STATUS: RUNNING
AREA: claude-github-tools
LEASE_OWNER: Codex/claude-protected-main-fix
START_UTC: 2026-10-20T14:16:48.045517+00:00
EXPIRES_UTC: 2026-10-20T14:56:48.045517+00:00
BASELINE_PROVEN: source b6093714914ff2c1e544e4cf867c04215ee8ac4b; GitHub/GitLab github-bridge blob c20bc84bc44ae37bb55a27cc7e243dbe0e126f62 equal. Active ruleset 25443611 requires PRs for main with no bypass actors. Only legacy Claude lease expired 2026-10-19T12:33Z. No concurrent MCP CI/deploy observed (only unrelated CORTES).
FAILED_AVOIDED: begin-task writes its lease directly to protected main and maps upstream errors to generic 409. Preserve main protection; move operational leases to fixed coordination branch, use atomic expected HEAD and read-back verification, honor legacy leases.
SUCCESS_SIGNAL: protected-main mocked regression, active-lease and stale-HEAD refusal pass; reviewed PR and official guarded deployment succeed.
FAILURE_SIGNAL: any main write, missing concurrency fence, legacy lease ignored, tests or deployment fail.
TEST_VALIDITY: unit mocks prove contract only; actual owner Claude invocation is separate acceptance. No forged OAuth and no publication probe.
SCOPE: GitHub bridge lease registration and tests only; no OAuth, CORTES, secrets or admin rule changes.
