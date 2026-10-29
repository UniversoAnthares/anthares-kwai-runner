# Item5 — Hostinger broker and C8 integration reconciled
STATUS: PARTIAL
AREA: anthares-remote / neon-idle-optimization / c8-hostinger-integration
DATE: 2026-10-29
OWNER: Work item5-hostinger-c8-20261029
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40935158539
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40935158539/job/123663639958
COMMIT: 19368d9d79a451e9bf39e7dbdb30d17aed6d37fa
SUPERSEDES: 20261029-item5-hostinger-c8-integration-lease.md; 20261028-ara-neon-c8-wake-subscriber-stage-c-running.md

## Result
Lease CLOSED. Source correction and offline acceptance PROVEN; live deployment
and end-to-end receipt remain NOT_PROVEN. No production/broker/secret changes.
Only six integration source/test/doc files changed in code commit. No local
work files, services, binaries or new agents created. Owned hPanel/File Manager
tabs866202516/866202519 closed; temporary external CI completed and cleaned up.

## Deployed source evidence
Authenticated hPanel anthares.us opened; File Manager failed ERR_CONNECTION_RESET
including one reload. Existing SSH read exact public_html/ara-notify/index.php;
SHA256537c6dfc5b54163b9a1cd7180e21dba21ca3bca05e5a33b236e0e2dbfe5b649c.
Broker not modified. Protocol is HTTPS JSON long polling, not WSS/HMAC:
GET health then GET wait with device_id=DESKTOP-FTDK0HP, since=N, seconds=20.
X-Anthares-Notify-Key holds independent listener token, or Authorization Bearer;
hash comparison uses listener_sha256. Publisher role applies only to action=signal.
200 health includes ok/protocol=ara-wake-v1/sequence/role=listener.
200 wait includes ok/protocol/sequence/wake=true or false.
POST signal accepts device_id JSON and separate publisher secret, returns202
ok/protocol/sequence, never command execution proof.

## Corrected integration
C8 now subscribes via fixed trusted HTTPS health/wait with protected
ANTHARES_WAKE_LISTENER_TOKEN, default-off ANTHARES_WAKE_ENABLED.
Bounded bodies, strict schema/duplicate/null checks, no redirects, sequence
coalescing, immediate canonical reconciliation at connect/disconnect,
2s fallback and12s safety scan preserved. Quota402/429 or auth401/403 terminates
subscriber attempt instead of waiting/retrying quota. Jobs still acquired by
original pollJob path; global semaphore, independent Git queues, canonical
leases, idempotency, encrypted result replay and heartbeat60s unchanged.
Copied existing Hostinger sender/tests from PR1815 verbatim into PR1808,
removing its incompatible Cloudflare sender without adding a second emitter.
Prototype Cloudflare files retained isolated; not promoted/deployed.
Docs now describe exact protocol and deployment gates.

## Decisive validation
Run40935158539, exact code commit19368d9:
- Node notifier7/7 PASS; existing isolated Worker contracts7/7 PASS.
- go mod verify: all modules verified.
- go test -count=1 ./...: agent PASS15.066s, existing regression package included.
- Windows amd64 cross-build succeeded.
- ARA_WAKE_NOTIFICATION_ONLY_CONTRACT=PASS.
- ARA_WAKE_C8_OFFLINE_TESTS_AND_WINDOWS_BUILD=PASS.
- Binary SHA256309a7a15485897b7d75327b35efb1e85fcf7768b275d1171592d3c3cf2156262.
- Artifact12925355300, anthares-c8-wake-candidate, expires2026-11-05.
- Separate CI Primary40935158510 completed success.
Go tests cover health/wait cursor advancement, idle, cancellation/resource
closure, duplicate wake coalescing, schema injection, sequence regression,
auth/quota termination and credential non-forwarding across redirects.

## Live boundary
Existing Hostinger listener.token read only within Hostinger process and
checked against configured hash: listener_hash_matches=true, device_matches=true.
No secret value/hash was emitted. HTTPS health returned403 Server:hcdn,
Content-Type:text/html, no WWW-Authenticate (not broker JSON).
No authenticated health/wait success or POST signal asserted. No state write.
No protection weakened, identity changed, proxy/CDN bypass or duplicate retry.
Original successful broker acceptance documented by owner remains historical.

## Deployment information for item5
Do not merge this old branch wholesale over concurrent production work.
PR1815 notes effective Cloudflare gateway executes against Vercel reserve;
its sender was installed on primary only. Reconcile exact deployed controller,
then ensure ONE post-commit Hostinger publisher, private listener provisioning
to SAME C8 process, signed/exact binary provenance, supervisor/last-good retention,
authenticated broker health/wait and one harmless canonical job end-to-end
without duplicate execution. Rollback: wake flag OFF. Deployment remains pending.
No additional fixed-list item added; no CU-hour savings/autosuspend claimed.

Governance loaded: REGRAS CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138;
INDICE2EFAB2052ABDD9083FAB5DA6E489846E0AA75C7A8097C576AAE5D0BDE0A69D12;
PROMPT BF5967D3D36854AA9FD3AC7831D26FE67933BDF995476091DC4F4A1CA6EA69BE.
GitHub branch fenced to exact expected HEAD; peer GitLab feature ref absent
(404), main inspected, no mirror mutation or production merge.
