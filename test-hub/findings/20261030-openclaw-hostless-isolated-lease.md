# OpenClaw Hostless validation — isolated lease
STATUS: PARTIAL
AREA: openclaw-cloud-hosting
DATE: 2026-10-30
RUN: none
JOB: none
COMMIT: isolated branch aoi/openclaw-hostless-validation-20261030
SUPERSEDES: none
LEASE_OWNER: ChatGPT/aoi-openclaw-hostless-20261030
LEASE_SCOPE: only hostless.yaml and infra/openclaw-hostless/ on isolated branch
BASELINE_PROVEN: Northflank free max 512 MB per service, TikTok/ARA preserved; Hostless docs advertise free pooled 0.5 vCPU and 1024 MB.
FAILED_AVOIDED: ClawCloud closed May 2026; Hostless permanent volumes cost extra and are not part of free entitlement.
SUCCESS_SIGNAL: authenticated Hostless free account, build success, continuous HTTP and WebSocket probe, volume persistence across restart before any real credentials.
FAILURE_SIGNAL: deployment rejected, memory OOM, missing writable state, missing websocket, payment required or failure to preserve SQLite state.
TEST_VALIDITY: no live launch authorized until billing and persistent-storage eligibility are established in account. No publishing, secrets, local PC files or existing service change.

## Scope
Prepare a fail-closed, disposable OpenClaw Gateway image and Hostless deployment manifest. The container requires its own ephemeral Gateway token and cannot hold real integrations or sessions until persistent local SQLite is established under the user's R$0 policy. This lease is restricted to a new isolated GitHub branch.
