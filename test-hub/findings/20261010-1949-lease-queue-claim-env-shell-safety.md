# Lease: queue claim environment serialization hardening
STATUS: RUNNING
AREA: queue
DATE: 2026-10-10
OWNER: automation-anthares-video-queue-env-1949Z
LEASE_UNTIL: 2026-10-10T20:14:00Z
HEAD_BASELINE: 25552f980b8901ec8c87797aed4d8eccc1e916e2
RESOURCES: kwai_claim_job.sh, kwai_run_next_job.sh, tests/test_kwai_claim_env_safety.py
BASELINE_PROVEN: Cloudflare v16 fencing and heartbeat tests are PROVEN; canonical kwai_run_next_job.sh executes source on a temporary file populated with unquoted queue metadata by kwai_claim_job.sh.
FAILED_AVOIDED: no Android login reruns, no publication, no use of exposed credentials, no lease mutation in Cloudflare, no repetition of failed heartbeat tests.
SUCCESS_SIGNAL: adversarial source title with shell metacharacters/newlines cannot execute commands or override fenced lease generation; round-trip values and safe claims are validated on exact SHA by hosted CI.
FAILURE_SIGNAL: sourced title executes command, injects environment variables, changes lease generation, or normal title/claim breaks.
TEST_VALIDITY: synthetic queue claim and local shell test only; no assertion of real Kwai publication or authenticated session.
