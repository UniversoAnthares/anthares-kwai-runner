# Lease: Kwai LIVE cloud E2E
STATUS: RUNNING
AREA: kwai-live
DATE: 2026-10-06
LEASE_AREA: kwai-live
LEASE_EXPIRES: 2026-10-06T12:00:00Z
BASELINE_PROVEN: Cloudflare routing selects hls_origin -> github and failover self-test is PROVEN; anthares-clipper contains finite supervised Kwai RTMP session code with ingest confirmation, heartbeat, restart limits and cleanup, but the current high-level controller remains disarmed and old wrappers contain local-PC defaults.
FAILED_AVOIDED: do not restore Windows/MEmu/schtasks runtime; do not start a long live before auth/session/source preflight; do not leave a room active after a failed canary.
SUCCESS_SIGNAL: GitHub-hosted cloud canary proves authenticated Studio session, room creation, RTMP ingest, official start result=1, live roomStatus=1, heartbeats, stop/cancel cleanup result=1; no PC path involved.
FAILURE_SIGNAL: storage state invalid/expired, Studio surface changed, ingest not confirmed, or cleanup not confirmed. Fail closed and create/repair cloud bootstrap before retry.
TEST_VALIDITY: repository-secret state only, synthetic owned media generated inside runner, finite <=120s initial canary, explicit --activate required, cleanup in finally, no secret/state logging.

Objective: replace the disarmed/local LIVE path with a self-contained GitHub-hosted executor and prove it end-to-end.