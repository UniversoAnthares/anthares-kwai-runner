# AOI #16 — Pinterest apex origin acceptance fix
STATUS: PARTIAL
AREA: pinterest-browser-origin
DATE: 2026-11-09 UTC
ITEMS: [16]
LEASE: CLOSED
SUPERSEDES: lease-20261109-aoi16-pinterest-apex-origin.md
SOURCE_ISSUES: #1978, #1981
BASE_GITHUB_HEAD: 8efc7079c4f7a5ec14fdfce0c60d74669c842006
TARGET_BLOB_BEFORE: 2b517f082ed71404200e036ffc3334d630cb8b2b
TARGET_BLOB_AFTER: 8d7d31657d8d1332b9536edd3c708b0eaff45926
PATCH_COMMIT: d4e1dfc9878faaded5c93fb5e1b26555efa7b5d8
PEER: GitLab anthares-kwai-runner main content equal before patch.
CHANGE: session(p) permits the exact `pinterest.com` host already allowed by page(url), while preserving the `.pinterest.com` subdomain rule. Lookalike domains remain denied.
QA_STATIC: Node 22.16.0, six directed allowed/denied hostname assertions PASS; one-line JS predicate only; no CI, Chrome session, media or network publication triggered.
ACCEPTANCE_LIMIT: Original failed browser href was sanitized; original P0 causal closure and a real authorized publication remain UNVERIFIED. Do not resend uncertain content or promote AOI 16 to DONE based on this code patch.
COST_ADDED: zero
