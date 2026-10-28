# ARA C8 SYSTEM wake subscriber — source implementation
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization
DATE: 2026-10-28
RUN: GitHub Actions CI pending
JOB: none
COMMIT: feature/ara-wake-hibernation-20261028
SUPERSEDES: none

## BASELINE_PROVEN
Current canonical agent runs as SYSTEM from
C:\ProgramData\AntharesRemoteAgent\anthares-remote-agent-v4-c8.exe.
Live vcs.revision ab6c668cb323c7606c63e175830c86e3f80c81be and live
SHA-256 4FFEFC590D6825BA946373DBDC31F8D61C0B07932807F0C606A2275471FD609C
were identified in the earlier live verification; recertify before deploy.
The source includes one process-global execution semaphore for HTTP and
independent GitHub/GitLab issue queues.
Stage A Worker contracts PASSED in CI run 40760638379; Stage B notifier
contracts PASSED in CI runs 40761131838 and 40761647955.

## Implementation
New wake_subscriber.go uses fixed authenticated WSS transport, message
validation, WebSocket ready/wake event coalescing, bounded reconnect/liveness,
12-second safety reconciliation while socket is healthy, immediate 2-second
polling on failure, same HTTP lease path and no new process or file spool.
Feature flag ANTHARES_WAKE_ENABLED defaults OFF. Current Neon heartbeat
every 60 seconds is intentionally unchanged.

## FAILED_AVOIDED
The new socket is not a job source or execution authority. No Cloudflare
Worker/Vercel deployment, no principal secret or Windows C8 binary alteration.
No social publisher, OAuth/lease state or database mutation. Fail-closed
on untrusted WSS endpoint or device identity.

## SUCCESS_SIGNAL
GitHub Actions runs Go unit tests, original C8 regression tests, and a
Windows/amd64 cross-build under the Go 1.22 module. Tests confirm socket
ready/wake/disconnect, coalesced notifications, 12s reconciling and 2s
fallback and reject any job-shaped payload. Exact CI run SHA required.

## TEST_VALIDITY
CI compile/build success is NOT a live agent deployment, original
GitHub/GitLab failover test, or Neon CU-hour reduction measurement.
Implementation remains isolated until the previously defined gate is met.
