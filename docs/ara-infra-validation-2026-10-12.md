# Anthares Remote Agent — infrastructure validation (2026-10-12)

Branch: `feature/ara-infra`

## Proven on isolated Render canary

Service: `anthares-ara-infra-canary-v2`

- Explicit ARA app entrypoint boots successfully on Render.
- `GET /v1/public/status?device_id=DESKTOP-FTDK0HP` returns HTTP 200.
- Missing device token is rejected with HTTP 401 on device heartbeat and next-job endpoints.
- Missing controller token is rejected with HTTP 401 on controller status endpoint.
- Idempotent public ping creation returns the same job id for the same idempotency key.
- 20 simultaneous unique ping creations returned 20 unique job ids and queue depth 20.
- An unconsumed ping transitions from `queued` to `expired` after its expiration window.
- A queued job in the explicit volatile fallback disappears across Render redeploy. This is the reproduced failure that the Postgres store is intended to remove.

## Durable backend implemented

`ara_state_store.PostgresStore` provides:

- durable heartbeat rows;
- durable jobs/results;
- idempotency key uniqueness;
- lease expiry and requeue;
- job expiry;
- `FOR UPDATE SKIP LOCKED` queue leasing;
- terminal-result idempotence.

A GitHub Actions workflow includes a real `postgres:16` service and tests store recreation for heartbeat, queued job, expired lease recovery, and result persistence.

## Render database

Free Render Postgres `anthares-ara-state` exists and is available.

The current Render connector intentionally does not expose the generated database password/DSN and its web-service environment API only accepts literal values; therefore it cannot securely bind the database to the canary from this connector alone. External MCP SQL access is also blocked while the database IP allowlist is empty.

No database credential is committed to GitHub.

## Windows evidence status

`DESKTOP-FTDK0HP` is currently unreachable through AI Commander and Remote Desktop Commander, and the ARA public status reports no fresh heartbeat. Real PC reconnect/ping execution remains pending connectivity; no reboot was attempted.
