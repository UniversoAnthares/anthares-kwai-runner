# Lease: dedupe/state acceptance 5-way
STATUS: RUNNING
AREA: kwai-qa-dedupe
DATE: 2026-10-05
LEASE_AREA: kwai-qa-dedupe
LEASE_EXPIRES: 2026-10-06T03:15:00Z
BASELINE_PROVEN: canonical interval gate; legacy quarantine; v16 queue fencing; five independent heartbeat probes.
SCOPE: tests/workflow/findings only. No kwai-login mutation and no real publication.
SUCCESS_SIGNAL: five distinct dedupe/state invariants execute concurrently; then production queue self-test is re-run if compatible.
