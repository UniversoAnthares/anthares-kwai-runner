# Anthares Remote — Notifications before Neon polling
STATUS: STAGE A CODE ONLY (NOT DEPLOYED / NOT LIVE)
DATE: 2026-10-28

## Additional fixed tasks
8. Build authenticated wake-only notification transport on existing external cloud.
9. Add a feature-flagged post-commit notification to canonical Vercel/Neon controller.
10. Integrate canonical SYSTEM C8 agent with real wake events and safe legacy fallback.
11. Prove roundtrip, failover, no duplicates, Neon suspension and real CU savings.

## Baseline, verified 2026-10-28
- Windows executor: DESKTOP-FTDK0HP, SYSTEM, C8 Go agent at C:\ProgramData\AntharesRemoteAgent\anthares-remote-agent-v4-c8.exe.
- Binary Go vcs.revision ab6c668cb323c7606c63e175830c86e3f80c81be (older than GitHub main), binary SHA-256 4FFEFC590D6825BA946373DBDC31F8D61C0B07932807F0C606A2275471FD609C. Reconfirm before replacing anything.
- Existing independent private GitHub and GitLab issue-queue transports, exact job ID dedupe and global C8 concurrency must not change.
- Vercel anthares-remote-primary is canonical MCP/controller; Neon anthares-ara-ha, project purple-flower-35918989, main neondb, holds real jobs, leases and OAuth replay state.
- Source agent idle wait: 2 seconds, plus Neon-backed heartbeat every 60 seconds.
- Source Vercel leaseNext calls reap even when empty; reap performs four SQL updates, then a reservation transaction.
- Period usage about 77 CU-hours was observed; exact per-query CPU cost has NOT been measured.
- Cloudflare previously exhausted shared Durable Object write quota. Check current quota before any deploy. Existing DO services stay untouched.
- Production social publishers / public queues are outside this optimization.

## Phase A: isolated wake-only Cloudflare Worker (this PR only)
New isolated app in cloudflare-ara-wake directory; private job content never
passes through notification transport.
GET /health: config readiness, not Neon.
GET /connect?device_id=DESKTOP-FTDK0HP: WebSocket 101 only for a bearer matching
the existing trusted device-token SHA-256 public fingerprint at
anthares-remote-agent/devices/DESKTOP-FTDK0HP.sha256. If hash retrieval fails,
fail closed. The existing HTTP queue continues unaffected.
POST /notify: exact JSON (device_id, kind=jobs_available, created_at_ms, nonce)
authenticated with HMAC-SHA256 and X-ARA-Wake-Timestamp (milliseconds),
X-ARA-Wake-Signature. HMAC covers timestamp + LF + exact body.
Reject unknown device, malformed/oversized payload, timestamp outside 30 seconds,
and invalid signature. A replay inside the window can at most cause an extra
notification: zero commands/jobs/leases are created.
Durable Object accepts WebSockets in hibernation mode with an attached device
identifier and sends only type=wake, at_ms and a random UUID. No SQL, KV, storage
writes, shell commands, quotas, pricing or publication operations.
Cloudflare protected secret ARA_WAKE_NOTIFY_SECRET is not committed.

## Phase B: post-commit notifier (NOT YET IMPLEMENTED)
Read full live controller, gateway and deployment configuration plus Test Hub.
Only after canonical Neon INSERT commits may Vercel send authenticated wake.
A wake never creates a second job. If wake fails, persist the job and preserve
the existing active two-second poll. Do not claim receipt from delivered=0.
Use bounded request timeouts so an upstream Cloudflare outage cannot block
user-facing MCP execution. Do not send credentials or shell arguments.
Use a flag defaulting OFF, a separate secret and exact commit pin before
deploying Vercel.

## Phase C: existing C8 subscriber (NOT YET IMPLEMENTED)
Add a flag (default OFF) in the SAME C8 process, no new PC daemon/cache/files.
Use existing Go device bearer token; if socket opens, perform one canonical
drain immediately to close the subscribe/enqueue race, then drain on wake events.
Always lease on canonical Neon, with existing ownership, idempotency, SAFE_RETRY
and UNCERTAIN semantics. Preserve all GitHub/GitLab queue processors and
global MAX_CONCURRENT budget.
If WebSocket disconnects, is rejected, loses a heartbeat or becomes ambiguous,
fall back to existing two-second polling immediately; reconnect with bounded
backoff/jitter. Do not wait 5+ minutes: existing jobs have bounded expiration.
Preexisting agent heartbeat every 60 seconds must initially remain active, even
though it prevents Neon autosuspend. Only after socket/presence semantics are
proven may that heartbeat be decoupled from Neon in a separate guarded phase.
Do not present stale online status as real connected status.

## Phase D: acceptance/rollback (NOT YET STARTED)
- Offline protocol tests pass, no production deploy.
- Check Cloudflare shared limits/secret and deploy *new isolated* Worker only.
- Unauthorized connection/notify returns 401, authorized socket returns 101.
- One harmless authorized real ping through original Neon lease/fence.
- Handle queued-before-subscribe, lost wake, socket disconnect, 401/403, 429,
  Cloudflare outage, restart, concurrent workers, duplicate wake and expired lease.
- Confirm session_status freshness even if Neon temporarily suspends.
- Observe actual Neon >5 minute suspend, then live wake; measure equivalent
  before/after windows and report p50/p95 latency, active time and CU-hours.
- Source, CI, READY or a socket handshake are NOT equivalent to live CU savings.
- Rollback is flag OFF; restore original polling/heartbeats and existing
  supervisor. No reboot, no second runner or new local artifact.


## Stage B implementation in same draft PR (source only)
- Added vercel-ara-primary/api/wake-notifier.mjs and an isolated test module.
- The Vercel route createJob sends a wake only AFTER the Neon INSERT/UPSERT
  returns. It is gated on ARA_WAKE_NOTIFY_ENABLED=1, default disabled.
- Protected secret ARA_WAKE_NOTIFY_SECRET must be configured independently
  on Cloudflare Worker and Vercel, never committed or logged.
- Notification target URL is an exact, hard-coded Cloudflare Worker endpoint.
- Request has 900ms cap, no retries or job resubmission, fail-open for the
  original persisted job and the existing 2-second poll.
- delivered=0 is recorded as unacknowledged notification, not completed job.
- No code/configuration in this PR enables the feature in production.
- DO NOT deploy the production Vercel controller before Stage B CI and
  Stage A Worker cloud quota/security review are accepted.


## Stage C: canonical agent subscriber (code staged, OFF by default)
- Go package: anthares-remote-agent/cmd/agent/wake_subscriber.go.
- Existing C8 main loop uses the same executionSemaphore for HTTP and
  GitHub/GitLab; new transport never executes a command itself.
- New opt-in env flag ANTHARES_WAKE_ENABLED=1, default OFF. When disabled,
  the exact 2-second idle poll and 60-second Neon heartbeat remain unchanged.
- A WSS connection is attempted only with the authorized device identity,
  existing device bearer, fixed trusted origin and no redirects.
- Valid Worker "ready" triggers an immediate original queue scan, closing the
  subscribe-before-enqueue race; each valid "wake" triggers another scan.
- WebSocket payloads cannot include commands, arbitrary job IDs, URLs or
  shell arguments. Every job is still leased from the canonical HTTP endpoint.
- A healthy socket reduces empty HTTP polling from every 2 seconds to a
  12-second bounded safety scan. This is essential because the Worker reports
  socket writes rather than durable device acknowledgments and a job may
  expire in as little as 31 seconds. A 5-minute scan could lose commands.
- A disconnected/auth-failed/malformed/stalled socket restores 2-second
  HTTP polling; "ready" and disconnect wake the main poll loop immediately.
  Reconnect uses bounded 2–33-second backoff with jitter, without any new
  Windows service, process, file spool or queue.
- WebSocket liveness messages are exchanged with Cloudflare (no Neon traffic);
  heartbeat to the canonical controller is intentionally UNCHANGED.
- The external dependency is github.com/gorilla/websocket v1.5.3, pinned with
  official module hashes in go.sum. No new network process is installed.
- CI tests validate parsing, auth flag default OFF, connected/fallback idle
  intervals, local WebSocket ready/wake/disconnect and Windows cross-build.
- Live C8 binary is older than latest source; require exact build provenance
  and existing supervisor/last-good integrity verification before replacement.

## Deployment gate — still CLOSED
1. Worker (item 8) must be deployed and pass authorized WSS + HMAC proofs
   without consuming paid Cloudflare quota or changing another ARA DO.
2. Vercel notifier (item 9) must be deployed with matching secret; only
   enable after safe queue transaction and delivery behavior are proven.
3. Build the exact Go Windows agent commit that includes this source, verify
   SHA-256 and run pre-/post-change real command roundtrip via HTTP and both
   GitHub/GitLab private issue queues, without duplicate execution.
4. Enable ANTHARES_WAKE_ENABLED only after the wake source is independently
   ready. Preserve last-good C8 and original SYSTEM supervisor; no reboot.
5. Item 11 must measure resulting Neon compute activity and separately
   address the still-live every-minute heartbeat, whose traffic can keep
   the Neon main branch awake even with reduced empty queue polling.
