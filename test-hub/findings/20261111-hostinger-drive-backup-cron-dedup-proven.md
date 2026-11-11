# AOI7 Hostinger — Drive backup duplicate cron removed, production readback
STATUS: PROVEN_SCHEDULE_DEDUP_RESOURCE_REPAIR_PARTIAL
AREA: architecture/hostinger-nproc-duplicate-drive-cron
OWNER: chatgpt-20261111-hpanel-drive-cron
DATE_UTC: 2026-11-11T12:44Z
LEASE: CLOSED
PREVIOUS_LEASE: 20261111-hostinger-drive-backup-cron-dedup-lease.md
ORIGINAL_HISTORIC: 20261111-aoi7-hostinger-nproc-boost-temporary.md
COST_ADDED: 0
PUBLICATIONS: 0

## Production evidence — authenticated owner hPanel
- At 12:36Z Cron Jobs of anthares.us showed 10 tasks plus header.
- Identical Drive backup commands and schedule */15 * * * *:
  - redundant: /bin/bash /home/u566597497/bin/anthares-drive-backup.sh sync oldest
  - retained: /home/u566597497/bin/anthares-drive-backup.sh sync oldest >> /home/u566597497/.anthares-drive-backup/worker.log 2>&1
- Real Ver resultado for redundant/no-log: 2026-11-11T12:30:17Z SYNC RESULT uploaded=0 deferred=0 failed=0 attempted=0.
- Real Ver resultado for retained/logged: 2026-11-11T12:30:03Z Other backup worker already running; exiting safely. This proves competing duplicate cron workers.
- Removed ONLY the redundant /bin/bash sync oldest row by hPanel exact row Remover action. Hostinger notified Tarefa cron excluída com sucesso.
- After a new page load, hPanel readback: rows=10 including header (9 cron tasks), backups=1, retained_with_worker_log=1, unlogged=0, forgejo_keepalive=1, Kwai kw12=1, Forgejo mirrors=2. All unrelated cron jobs preserved.
- No files or backup data deleted, no process terminated, no post/uploads, no payment.
- Operator goal: reduce duplicate startup overhead and self-lock contention every 15 min. A single retained worker should run backup normally when its prior competing worker is gone, but the NEXT actual backup result after removal was not yet observed.

## Limits of closure
- The duplicate Drive backup schedule is permanently corrected.
- The root cause of NPROC spikes remains UNPROVEN; the Hostinger dashboard previously recorded quota hits at 80 and the free 24h capacity boost to 120 expires around 2026-11-12T12:09Z.
- Other jobs include minutely KW12 cron, five-minute git sync and Forgejo keepalive, half-hour mirror and hourly AVS; these were not edited.
- Explicit Hostinger external process inventory refusal respected; no alternate command executor or arbitrary cron created.
- The Forgejo HTTPS public endpoint and complete mirror SHA parity still need independent authorized attestation. Keep AOI7 broader status PARTIAL.
