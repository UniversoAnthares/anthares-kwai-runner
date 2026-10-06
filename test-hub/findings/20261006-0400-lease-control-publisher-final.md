# control-publisher integration final lease
STATUS: RUNNING
AREA: control-integration
DATE: 2026-10-06
LEASE_AREA: control-publisher-integration
EXPIRES: 2026-10-06T04:20:00-04:00
BASELINE_PROVEN: QA5 run 37405502253; Cloudflare v16 fencing; publisher heartbeat/fencing.
FAILED_AVOIDED: no real Publish; no Android/login mutation; stale generation crossing publisher boundary.
SUCCESS_SIGNAL: expanded integration matrix passes canonical identity, generation, renew, crash, uncertain, idempotency and promotion gate.
FAILURE_SIGNAL: stale holder or duplicate confirmed/uncertain crosses boundary.
TEST_VALIDITY: simulated lifecycle only; no claim of real Kwai publication.
