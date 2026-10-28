# ARA C8 Hostinger wake listener — isolated integration
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / c8-hostinger-wake
DATE: 2026-10-28
OWNER: ChatGPT GPT-6 — fixed item 5
RUN: pending
COMMIT: ea9efbe8b9b975aa6e36e554271b0254bc6b78aa
SUPERSEDES: none
LEASE: max 30 minutes. Separate C8 listener branch; do not modify concurrent reserve Vercel branch.

## BASELINE_PROVEN
Real SYSTEM C8 binary SHA256 4ffefc590d6825ba946373dbdc31f8d61c0b07932807f0c606a2275471fd609c and Go vcs.revision ab6c668cb323c7606c63e175830c86e3f80c81be. Source at ab6c668 and GitHub main has Go main.go blob 13172ffe3dac06dddd92874020fa489ed02bdffe, GitLab main matches same blob. Device canonical https://anthares-remote-primary.vercel.app with protected independent GitLab/GitHub queues and one executionSemaphore. Hostinger https://anthares.us/ara-notify/index.php has authenticated read-only health/wait; protected reserve Vercel emitter accepted sequence 17 and Hostinger monotonic counter advanced to 25. PR #1808 Cloudflare WSS stage is separate and not deployed; earlier attempt to create another Go module was security-blocked. The design here is materially different, implemented only as minimal changes to existing source and no remote credential handling in write tool.

## FAILED_AVOIDED
No new Windows process/service, no alternate job/lease source, no Cloudflare DO, no extra durable files, no secrets committed/echoed, no auto-deploy to production, no mutation of Vercel/Neon schema, source of commands, Git private queues, OAuth, job results or idempotency. Keep 2s polling when broker disabled/unavailable. Never use existing device bearer token to authenticate to Hostinger; use separate opt-in listener credential. Limit wait to 20s and keep 12s safety reconciliation. Preserve existing supervised C8 binary until acceptance and last-good evidence. Respect prior security denial; do not retry refused external_wake.go write.

## SUCCESS_SIGNAL
Main code diff only wake event subscription, strict fixed HTTPS origin, independent listener token, bounded parsing and timeouts, immediate 2s fallback, 12s healthy reconciliation, no command-bearing notifications, existing semaphore. Go tests and Windows cross-build under immutable SHA succeed. Before production swap verify exact binary and original GitLab/GitHub and HTTP lease, supervisor state; after swap independent real roundtrip, no duplicate and fallback.

## FAILURE_SIGNAL
Compile/test failure, actual C8 SHA drift, active concurrent C8 lease, invalid host response/unauthorized, missing protected credentials, missing last-good/recovery or loss of Git queues.

## TEST_VALIDITY
CI compile/syntax and Vercel broker accepted are not live C8 acceptance; health session and actual job evidence required.
