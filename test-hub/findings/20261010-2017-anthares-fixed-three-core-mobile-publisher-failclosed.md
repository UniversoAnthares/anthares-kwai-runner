# Three immutable components: autonomous implementation and evidence
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38087104230
SUPERSEDES: none

## 1. Anthares Core — COMPLETE / PROVEN autonomous durable safe tasks
- Final acceptance run: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38087104230 SUCCESS.
- Cross-run durable-state proof succeeded from prior cloud run `38083961951` into independent cloud run `38087104230`: `ANTHARES_CORE_CROSS_RUN_PERSISTENCE=PASS`.
- The current run restored persisted state from `anthares-state`, imported it into a fresh SQLite database, processed allowlisted work, exported state and committed it back to `anthares-state` as commit `a7cb833`.
- Final gates emitted `AUTONOMOUS_CORE_SUPERVISOR=PASS` and `ANTHARES_CORE_ACCEPTANCE=PASS`.
- Cloud control watchdog emitted `ANTHARES_CORE_CONTROL=HEALTHY`.
- 13 Core tests passed in the final acceptance run, covering fenced leases, heartbeat, idempotency-key collision failure, bounded retries, expired-lease recovery, irreversible-job quarantine, state import/export and control watchdog behavior.
- Supervisor is scheduled every 15 minutes at minutes 7,22,37,52, with push/manual triggers. Schedule delivery is subject to GitHub scheduling latency and is not a hard real-time guarantee.
- Executor is GitHub-hosted Ubuntu; no local PC fallback is used by Core.
- Historical independent successful runs remain 38079229078, 38082768556 and state test 38082797061.

## 2. Anthares Mobile — PARTIAL, no live authentication
- UI parser now refuses to treat a typed username, feed text or onboarding page as authenticated profile.
- Tests: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38082486567 SUCCESS.
- Actual Android native UI remains without verified `@lucasrosalem` identity: run 38082538347 had 20 valid UI dumps, zero profile taps, no login chooser, and no crash/ANR. Known profile ID is not in bottom navigation. Do not blindly tap or claim login.
- No cross-run authenticated session restoration verified; no private encrypted session store confirmed.
- Existing previously exposed password must be rotated before credentialed publisher can resume.

## 3. Anthares Publisher — PROVEN static and fail-closed; no live post
- Atomic ledger prevents overlapping timecodes and same content SHA-256 across different source IDs for same account/platform.
- Unknown outcome quarantined; only explicit proven pre-submit failure may retry.
- Cloudflare queue `complete` and `reconcile` clients now require independent remote post ID, direct matching Kwai public URL, and unauthenticated HTTP reachability. No synthetic queue-job-derived post IDs.
- Tests: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38082877564 SUCCESS.
- No verified public Kwai post URL or post ID exists, so publication remains NOT PROVEN and must not be claimed.

## Execution constraints
- Cost: zero; no credit card; no local PC as executor; no user interaction used for these code/test changes.
- Production MR !34 and unrelated WordPress production code are not merged.
- Remaining end-to-end blocker: a legitimate authenticated Kwai session for the correct account that persists across two independent cloud executions, then one verified public post.
- Do not repeat failed Android UI diagnostics without a new causal hypothesis or new evidence. Never bypass OTP/CAPTCHA or Kwai security challenges.
