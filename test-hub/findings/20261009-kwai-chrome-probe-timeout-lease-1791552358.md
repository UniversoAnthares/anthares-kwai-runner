# Chrome remote probe timeout causal retry
STATUS: RUNNING
AREA: kwai-chrome-probe-runtime
DATE: 2026-10-09
OWNER: chatgpt-browser-runtime
RESOURCES: .github/workflows/kwai-chrome-session-probe.yml, .kwai-session-probe-trigger
LEASE_UNTIL: 1791553558
BASELINE_PROVEN: 37935956989 was cancelled after six minutes during combined dependency-install/probe step; no session-probe.json or identity evidence produced. Offline Chrome cache security QA 37936417696 passed 8/8.
FAILED_AVOIDED: split installation and browser probe with independent explicit timeouts; use already-bounded Chrome popup and method waits from e60ef388; do not rerun identical uninstrumented 6-minute step.
SUCCESS_SIGNAL: hosted Chrome run completes with KWAI_SESSION_PROBE JSON and authenticated=false until explicit identity proof, without plaintext cache.
FAILURE_SIGNAL: dependency installation or browser probe fails with identified step and bounded timeout.
TEST_VALIDITY: browser-only Ubuntu runner; no Android emulator or user PC; no login or upload claimed.
