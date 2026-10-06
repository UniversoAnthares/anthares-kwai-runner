# Real Kwai publication workflow promotion gap
STATUS: PARTIAL
AREA: kwai-publish
DATE: 2026-10-06

Audit of .github/workflows/kwai-real-publish.yml shows that enable_real_publish=YES does not invoke kwai_publish.sh. The queued-publication-contract only validates canonical interval fields, and the guard intentionally exits 1 with: "Real publication remains gated until the kwai-publish acceptance workflow is promoted."

This is not a regression in the publisher itself. The publisher/heartbeat/fencing path is independently PROVEN. It is an integration/promotion gap between the production workflow and that protected publisher.

DECISION: do not silently claim end-to-end real publication is enabled. Promotion must occur only after independent kwai-login/session readiness, then acquire/load canonical queued job including KWAI_QUEUE_JOB_ID + KWAI_LEASE_GENERATION and invoke kwai_publish.sh under its existing heartbeat.
