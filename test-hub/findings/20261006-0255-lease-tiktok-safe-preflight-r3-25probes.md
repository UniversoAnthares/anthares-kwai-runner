# TikTok safe preflight round 3 lease
STATUS: RUNNING
AREA: tiktok-safe-preflight-r3
DATE: 2026-10-06
OWNER: CHAT 3

SCOPE: five repetitions of each of five non-mutating contracts (25 probes total).
BASELINE: Render identity/session positive; invalid/no-token paths must fail closed; Cloudflare public health positive.
EXCLUDES: queue-adapter negative-contract lease owned elsewhere; media-harness lease owned elsewhere; no enqueue/lease/started/publish.
SUCCESS_SIGNAL: each contract produces 5/5 consistent outcomes.
FAILURE_SIGNAL: inconsistent auth behavior, loss of Render identity, or public control health failure.
