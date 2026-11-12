# SEC-01 — Threads BWS metadata audit (isolated QA)
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-25
OWNER: chatgpt-sec01-threads-bws-metadata-qa
BRANCH: chatgpt/sec01-threads-bws-metadata-qa-20261025
BASELINE: 183f6a8eda4d2585f6cdd73982984a66df541802
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none

## BASELINE_PROVEN
The existing Bitwarden sm-action accesses a known Threads secret UUID in cloud workflows; Gemini workflow run 40214777894 demonstrated successful SDK machine-account login and secret lookup via client.auth().loginAccessToken. Prior CORTES BWS metadata diagnostic 39511953159 failed during authentication with a different SDK invocation. The reference for the sole scoped account is config/threads-cloud-auth-reference.json. Governance GitHub manifest version 2e28d54043d6bad1, local Windows preflight PASS with version f6fc9ca59a96e451; discrepancy preserved without overwriting.

## FAILED_AVOIDED
Do not repeat old client.loginWithAccessToken API, print/access token values, disclose secret material, change BWS ACL, elevate access, use a second principal as an escalation, modify production workloads, send posts, or touch queue. Use read-only SDK calls for the single Threads ID, then delete temporary SDK/session files.

## SUCCESS_SIGNAL
SEC01_AUTH=PASS; SEC01_THREADS_SECRET_METADATA=PASS; SEC01_SCOPE_PRESENT=PASS, with organization/project IDs returned only as presence booleans; optionally SEC01_LIST_SCOPE=PASS if metadata list is authorized. The evidence is only scoped credential reachability; machine account name/plan quota require provider admin metadata.

## FAILURE_SIGNAL
SEC01_ERROR_STAGE and nonzero exit. A denial is recorded as denial and not bypassed, no fallback to unrelated principals.

## TEST_VALIDITY
One manual/no-publication GitHub-hosted workflow on a unique QA branch, using the existing GitHub Actions BWS_ACCESS_TOKEN secret and pinned official Bitwarden SDK. Scoped runtime must never print or persist token/secret values. Main remains unchanged. No production cutover or claim of cross-account isolation from a positive-only smoke test.
