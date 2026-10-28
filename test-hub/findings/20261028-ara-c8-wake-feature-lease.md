# ARA C8 — sinalização externa com fallback
STATUS: RUNNING
AREA: queue / ara-external-wake-C8
DATE: 2026-10-28
OWNER: GPT-6 Anthares Neon CU
BASELINE_PROVEN: main bdfdc6c5f9564247a5307a59b6a6a7b66dcc2414; production C8 binary inspected on 2026-10-28; original poll 2 seconds; heartbeat 60 seconds; independent GitHub/GitLab issue queues remain active; GitLab peer file main.go blob 13172ffe3dac06dddd92874020fa489ed02bdffe matches GitHub.
FAILED_AVOIDED: no production agent restart, queue mutation, credential migration, schema, deploy, or additional resident Windows service.
SUCCESS_SIGNAL: feature-gated wake protocol, canonical Neon lease acquisition preserved, loss-of-signal fallback, authenticated separate wake token and heartbeat, focused tests pass.
FAILURE_SIGNAL: unauthorized host/token exfiltration, skipped leased jobs, weakened replay/lease, test fail, concurrent file change.
TEST_VALIDITY: read full main.go, peer ref, source lease; no concurrent test-hub queue lease found for this specific area in latest main tree.
EXPIRY: 30 minutes after acquisition; final append-only finding closes lease.
