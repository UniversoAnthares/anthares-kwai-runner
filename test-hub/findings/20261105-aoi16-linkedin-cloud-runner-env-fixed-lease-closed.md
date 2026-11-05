# AOI #16 — LinkedIn cloud fanout runner identity fixed
STATUS: PARTIAL
AREA: qa-p0-linkedin-fanout-runner-gate
DATE_UTC: 2026-11-05T03:24:42.159Z
LEASE: CLOSED
SUPERSEDES: lease-20261105-aoi16-linkedin-runner-identity.md
ITEMS: [16]
CHANGE: `RUNNER_ENVIRONMENT: github-hosted` added at job env.
SOURCE_SHA: 00438f8fc9ed2dd00c4cccb692524cc28efc2433
PATCH_SHA: 198834abb653f6f00cadb15b0eddac19abf02c42
EFFECT: tools/cortes_linkedin_neon_fanout.py require_cloud() now receives exact runner identity from this workflow.
SCOPE: one env line. GitHub workflow disabled_manually before/after; no publication, replay, CI run, Neon mutation or cost. Overall #16 PARTIAL until live evidence.
