# Item fixo 16 — suprimir reemissão repetida de P0 Threads sem silenciar novas falhas
STATUS: PARTIAL
AREA: architecture/qa-p0-incident-remediation
DATE: 2026-10-29 UTC
RUN: one static/source patch and existing unit contract
JOB: none
COMMIT: dd6df2705f82c8cdcd0c505829d066ab4a6ac188
SUPERSEDES: none
LEASE: only tools/cortes_threads_continuity_guard.mjs + this finding; release on PR decision.

OBSERVED: GitHub Issues #1867–#1873 were opened in succession with exactly the same QA-P0-FINGERPRINT:0e91ae0664e3b5bda5f57d47, but with a new `threads-...json` file every approximately 30–35 minutes, matching the source's original re-alarm interval `30*60000`. The distinct issue numbers accidentally bypassed issue-number based QA executor cooldown.
IMPLEMENTATION: the upstream continuity guard now only recreates incident evidence of the identical problem fingerprint after twelve hours; changed fingerprints still escalate immediately. No change to scheduler cadence, source ledger, remote publication or existing forensic evidence. The controller's separate fingerprint-based dispatch dedupe was already merged in PR #1875 (SHA 87541dfb53bb0e17ac2d0e3b15062f9b11ebfe4a).
TEST_VALIDITY: existing `tests/threads_continuity_guard.test.mjs` verifies two successive invocations preserve `last_alarm_at`, identical fingerprint and exactly one incident artifact. This is a source-only safety regression; live repeated incident behavior needs later observation, not forced publishing or more QA runs.
SUCCESS_SIGNAL: single alarm per twelve-hour window per unchanged fingerprint, immediate alarm for changed problem set, no duplicate executor dispatch. Both P0 reporter fixes and remote publication correction remain separate gates.
LIMITS: none of the real Threads P0s were marked resolved; account/browser identity and publication NOT_APPLIED are not proven. Hence item 16 stays PARTIAL.
