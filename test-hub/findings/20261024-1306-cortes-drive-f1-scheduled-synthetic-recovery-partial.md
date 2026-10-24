# CORTES F1 — task agendada + réplica 2× e recuperação testadas
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-24
RUN: Anthares Remote jobs ef3b4717a902d0f03d920ce5267c4f40, 80d9b7121381710673ed1ce60d18e9ab, 8be770e73496a6024de097f9811ee6be, 6eb7fae2b5b3db7fe50dca16e19e4048, 6dd402890be436c8399066c6cdec0c22, bd8dc18fe119c1ce972d8d927867e049, 40605b9c82c8634c13c6bb6a15887d0c, 10cb41ea99047aa4113d1fbb3751260d, d74bd50eb3ab3dd52c3add8d231ba31f, f68a1701165b588aa29b450c1ce4354e
JOB: chatgpt-cortes-drive-f1-20261024
COMMIT: anthares-clipper replica guard blob 8fa0934c60e2401d31cffcb6f0b9d89740dd7402; TestHub lease PR #1305 merged as a2d34d6684226f1c054632801b1b4aa71983bb7a
SUPERSEDES: 20261020-cortes-three-google-drives-aux-storage-preauth.md

## Resultado verificado
- Windows SYSTEM Google Drive preflight: ready_count=2, profiles 3/9 have unique dedicated OAuth clients, valid authorized tokens, root folders and remote_probe=ok; profile2 excluded.
- Offline 21 tests passed (13 replica guard, 8 backup auxiliary) via unittest, no pytest installed.
- Synthetic QA MP4 of 10785 bytes sent to both Google Drive accounts by the real replica guard: status=verified; stored_replicas=2; verified_masters=1; failures=0; blocked_masters=0.
- Immediate rerun yielded stored_replicas=0 and verified_masters=1: checksum verified, idempotent.
- Independent rclone downloads from both Drives restored 10785 bytes per destination with matching local SHA-256.
- Installed protected SYSTEM-only runtime in C:\ProgramData\AntharesCortes\gdrive\runtime; runtime copy of guard, capacity and backup code hash-matched approved GitHub feature-branch files before copy. Did not merge broad cloud PR #190.
- Windows Task Scheduler task 'Anthares CORTES F1 Google Drive Replica 30min' registered as SYSTEM, hidden, PT30M repetition, IgnoreNew overlap policy, execution limit 3h, restart twice with 10-minute spacing. Verified manual run at 12:58 local and scheduled run at 12:59 local both LastTaskResult=0. Scheduled report correctly says idle_no_eligible_media, not backup success.
- Wrapper rotates media selection rather than repeatedly selecting the alphabetically first verified source; includes last-run.json, selection.json, and return codes.
- Controlled missing-rclone-config test failed closed with authorized_accounts=0 and exit code 2; re-established config recovered to verified with stored_replicas=0.
- Simulated orphan ledger lock for nonexisting PID recovered automatically and test completed verified. Artificial live-PID lock was preserved, returned exit code 2, and was cleaned by test harness only after proving fail-closed.
- Local protected runner-media/output and runner-media/shorts were checked: no eligible MP4 masters were present. No real production master backup can be claimed.

## Remaining acceptance and operational constraints
1. Wait for real eligible finished MP4 in runner-media/output or shorts, confirm two remote copies + SHA-256 + standalone restoration. No synthetic media should enter publication queues.
2. Observe repeated automatic invocations and source arrival, ensure no backlog/starvation or quota exhaustion, capture sanitized last-run report.
3. Version control the exact deployed standalone wrapper and conservative orphan-lock repair; reconcile with broad draft PR #190, respecting peer GitLab branch history.
4. Keep OAuth protected, profile2 unauthorized/excluded, preserve source masters and publisher isolation. Do not turn a no-media idle report green for real backup.
5. Lease area CORTES Drive F1 completed for this cycle with PARTIAL rather than production PROVEN.

## Evidence policy
No tokens, secrets, client IDs, or refresh credentials were copied to source control. Code/QA were applied under the user-authorized independent F1 storage scope. Scheduler is a local Windows dependency; no off-Windows runtime/failover of the scheduler was claimed.
