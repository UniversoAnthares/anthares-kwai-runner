# Three immutable components: autonomous implementation and evidence
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38082768556
SUPERSEDES: none

## 1. Anthares Core — PROVEN for autonomous durable safe tasks
- Core persists state in the `anthares-state` branch and has completed on two independent GitHub-hosted runs 38079229078 and 38082768556, without the user's PC.
- Scheduled supervisor now every 15 minutes, plus push/manual triggers. Schedule delivery can be delayed by GitHub; not a hard real-time guarantee.
- SQLite fenced leases, heartbeat, atomic idempotency-key collision detection and safe retry budgets implemented.
- Expired irreversible jobs transition to `uncertain` rather than auto-republishing. Probe tasks retry at most three times.
- Tests: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38082797061 SUCCESS.
- Cloudflare v16 `/health` independently verified HTTP 200 with queue_bound=true, persistent_state=true, pc_fallback=false.

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
