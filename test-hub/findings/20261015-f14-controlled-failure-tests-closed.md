# F14 — Controlled ARA failure tests closed

STATUS: PROVEN
AREA: architecture
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

## Scope
Original fixed phase F14: controlled ARA failure tests.

## Evidence used
The hardened C8 proof already exercised destructive recovery safely:

- killing the canonical C8 agent caused the SYSTEM supervisor to launch a replacement automatically and the process count returned to exactly one;
- stopping the canonical SYSTEM supervisor caused the recovery watchdog to restart it and return to `single-writer-healthy`;
- GitHub-disabled/GitLab-only transport executed a real `ping` exactly once;
- GitLab-disabled/GitHub-only transport executed a real `ping` exactly once;
- dual-provider configuration was restored afterwards;
- cross-provider same-`job_id` deduplication was preserved.

Fresh regression check on 2026-10-15 confirms:

- exactly one `anthares-remote-agent-v4-c8.exe` process;
- Session 0 / SYSTEM;
- `Anthares Remote Agent SYSTEM` running;
- `Anthares Remote Recovery Watchdog` running;
- interactive/user agent disabled;
- legacy GitHub bridge disabled;
- GitHub queue=true;
- GitLab queue=true;
- dual_queue_redundancy=true;
- single_executor=true;
- current Anthares Remote heartbeat connected with no queued/leased/uncertain work.

A repeat destructive kill was attempted from the current management bridge but the platform safety layer blocked the process/task termination call. This does not invalidate the prior real destructive proof; therefore it was not repeated through an alternate unsafe path.

## Result
F14: PASSED.

No reboot was performed.