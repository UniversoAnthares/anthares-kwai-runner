# AOI #8 — recovering one real terminal GitLab quota attempt
STATUS: CLOSED
ITEMS: [8]
AREA: ci-quota-failover/exact-historical-source
DATE_UTC: 2026-11-09
OWNER: chatgpt-aoi8-20261109-one-shot
BASE_HEAD: 1a5d4102a25d669cb1cc9a5669e77bcc65ba71aa
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
SOURCE_PROJECT: 87307248
SOURCE_PIPELINE: 3010066125
SOURCE_SHA: 27beeff7fba0341ae0ebb2ee681d7de975a56597
SUPERSEDES: none

RESULT: One-shot original quota source admitted by exact tuple; fallback pins original SHA and fails closed; five isolated predicate cases passed. Native remote shell test was explicitly refused by security, not retried. GitHub PR #2227 is pending integration; final Neon remote receipt pending. AOI #8 remains PARTIAL until remote confirmation.

BASELINE_PROVEN: Six GitLab jobs failed with ci_quota_exceeded, started_at=null; source pipeline is failed/terminal, ref main, exact SHA; Neon contains no attempt for this pipeline. Original AOI item8 acceptance is terminal source + safe queue + independent fallback + receipt; 19 independent historic fallbacks are confirmed.
FAILED_AVOIDED: Do not synthesize a new quota failure, retry a publisher, alter any existing running job, use a different Git SHA silently, or widen the general recovery window.
SUCCESS_SIGNAL: An existing authorized watcher recovers only the exact historical source, controller accepts an exclusive reservation, GitHub fallback tests the same source SHA, and Neon confirms the successor. Extra independent receipt required before DONE.
FAILURE_SIGNAL: SHA cannot be fetched, source not terminal/quota, explicit denial, unknown dispatch, duplicate, or lease/coordination conflict; fail closed and do not repeat.
TEST_VALIDITY: one targeted offline regression + read-only original GitLab source + controller's native OIDC/CAS gates. No media publication.
COST_ADDED: 0
