# ARA C8 Hostinger listener — candidate build, deployment blocked
STATUS: PARTIAL
AREA: anthares-remote / neon-idle-optimization / c8-hostinger-wake
DATE: 2026-10-28
OWNER: ChatGPT GPT-6, fixed item 5
RUN: GitHub Actions 40781599355 and 40781674578 (build success, tests not run by this workflow)
JOB: none
COMMIT: cad21f8fab736cbd5cca1493b2e5f5a170c25f5d
SUPERSEDES: test-hub/findings/20261028-ara-c8-hostinger-listener-lease.md

## Proven
The existing Go main.go blob 13172ffe3dac06dddd92874020fa489ed02bdffe matches the live provenance commit ab6c668 and GitLab main. In branch optimization/ara-c8-hostinger-poll-20261028, main.go blob ab24aadf40596396e1116d046c6261f05436d186 adds opt-in ARA wake listener using fixed HTTPS Hostinger URL, separate listener credential, no command payloads, 20s long-poll, immediate fallback to old 2s empty polling, and periodic 12s safety reconciliation when healthy. Existing heartbeat, single execution semaphore, OAuth HTTP job lease, encrypted result replay and independent Git queues unchanged. poll_capacity_test.go blob 27cb274aecc49fd26057da1e75ad56cee3499678 adds focused offline tests for fallback, protocol, credentials, malformed wake envelopes and bounds. CI Windows/amd64 cross-build succeeded in two runs; current production C8 binary unchanged, last confirmed SHA256 4ffefc590d6825ba946373dbdc31f8d61c0b07932807f0c606a2275471fd609c.

Canonical reserve Vercel is emitting Hostinger notifications: runtime logs show ara_wake_broker_accepted 14-17 and Hostinger persisted sequence advanced to 25, independent of primary Vercel project. Reserve source is managed under separate concurrent lease/PR #1817.

## Gate / Known defect
Not approved for production: readHostingerWake currently limits JSON decoder to 513 bytes but does not independently check that response length is <=512. Decoder can accept an otherwise valid JSON prefix followed by oversized whitespace. The included negative test detects this. A minimal correction was attempted on this GitHub branch but tool returned explicit OpenAI security-settings refusal; do not route around the denial or promote the candidate. The CI workflow only performs Windows cross-build, not go test. Source code is candidate only. Further test/deploy requires an authorized safe correction, proof from go test, exact binary integrity, supervisor last-good, protected listener token in SYSTEM environment, and real HTTP + GitHub/GitLab queue acceptance.

## Recovery and concurrency
No live Windows binary, processes, secrets, Hostinger service, Git queues, Vercel production or Neon schema changed by this branch. No extra PC process/service or state was installed. The original C8 remains active and continues legacy polling. Isolated lease closed as PARTIAL; do not count this as item 5 completed. PR #1808 WebSocket is a different unpromoted design.
