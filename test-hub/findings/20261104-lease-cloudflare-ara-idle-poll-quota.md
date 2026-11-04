# Cloudflare Workers Free — contenção de consultas ociosas ARA
STATUS: RUNNING
AREA: cloudflare-quota / ara-agent-poll
DATE: 2026-11-04
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none
OWNER: chatgpt-reestruturacao-otimizacao-20261104
LEASE_AREA: ara-agent-cloudflare-idle-poll-pacing
LEASE_EXPIRES: 2026-11-04T13:27:23.828Z
BASE_HEAD: d836fdeaf2fabfbb09fc570edb879f00fc0b9cf1
TARGET: anthares-remote-agent/cmd/agent/main.go
BASE_BLOB_SHA: 13172ffe3dac06dddd92874020fa489ed02bdffe
GOVERNANCE_MANIFEST: 223433740e807a90

BASELINE_PROVEN: Cloudflare Free 100000 incoming requests/day account-wide; owner email 2026-11-03 confirms exhaustion. Current main ARA agent polls every 2s idle and retries failures every 3s. This *can* generate 43200 idle polls/agent/day, plus 1440 heartbeats. Source: cmd/agent/main.go. Existing Cloudflare quota-guard coalesces DO state, which does not reduce incoming Worker requests.
FAILED_AVOIDED: no deploy, browser, local-PC runner, secret access, switching primary, unaudited retry, publication or billing; preserve pre-existing PRs #1808/#1920 (wake transport) without rewriting their branches.
SUCCESS_SIGNAL: small independent helper selecting 15s idle / 60s error for HTTPS *.workers.dev, unchanged 2s/3s for other providers, offline 8/8 unit tests, readback; new PR and merge only with safety/ownership reconciliation.
FAILURE_SIGNAL: change of base/source file, failing tests, merged overlap conflict, uncertainty about production.
TEST_VALIDITY: Go standard library tests in isolated sandbox, without contacting Cloudflare or remote devices. This fixes only source; productive improvement requires approved binary rollout.

Quantitative model: one idle ARA agent 44640 calls/day before, 7200 after (83.87% fewer) with 1/min heartbeat. Actual traffic ownership remains UNVERIFIED until authenticated Cloudflare per-worker analytics.
