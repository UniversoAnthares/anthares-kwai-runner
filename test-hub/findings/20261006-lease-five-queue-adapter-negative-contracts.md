# Lease: five queue adapter negative contracts
STATUS: RUNNING
AREA: qa
DATE: 2026-10-06
LEASE_AREA: kwai-queue-adapter-qa4
LEASE_EXPIRES: 2026-10-06T04:45:00Z
BASELINE_PROVEN: v16 adapter fencing and heartbeat QA.
FAILED_AVOIDED: no production queue mutation; HTTP/OIDC are stubbed locally.
SUCCESS_SIGNAL: five independent malformed/error contracts fail closed with no false ACK.
FAILURE_SIGNAL: malformed health/token/response or invalid generation can emit CENTRAL_*_ACK.
TEST_VALIDITY: isolated adapter contract.
