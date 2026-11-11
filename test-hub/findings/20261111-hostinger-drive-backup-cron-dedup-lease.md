# AOI7 Hostinger — Remover agendamento duplicado do backup Drive
STATUS: RUNNING
AREA: architecture/hostinger-nproc-duplicate-drive-cron
OWNER: chatgpt-20261111-hpanel-drive-cron
DATE_UTC: 2026-11-11
BASE_SHA: 2156c6cd7550f5a573bce316dd863e9086ea1d4a
HISTORIC_PROOF: 20261111-aoi7-hostinger-nproc-boost-temporary.md
SITE: anthares.us; Hostinger hPanel session authenticated in isolated AntharesTinyFish profile
CURRENT_STATE: 10 scheduled cron entries plus header; two identical */15 * * * * invocations of /home/u566597497/bin/anthares-drive-backup.sh sync oldest; one shell explicitly /bin/bash with no redirect, the other directly executable and stdout/stderr redirected to ~/.anthares-drive-backup/worker.log. In real 12:30 UTC cycle, no-log version reported uploaded=0 deferred=0 failed=0 attempted=0, logged version reported "Other backup worker already running; exiting safely"; this proves same work and lock contention.
CHANGE: remove ONLY */15 * * * * /bin/bash /home/u566597497/bin/anthares-drive-backup.sh sync oldest (no redirection). Retain */15 * * * * /home/u566597497/bin/anthares-drive-backup.sh sync oldest >> /home/u566597497/.anthares-drive-backup/worker.log 2>&1.
PRECONDITIONS: exactly 2 duplicate schedule rows, matching precise commands, only 1 selected removal; verify original count and post-removal count. Verify all other crons unchanged. No touch of backup files, secret or running process. No bulk process stop, no paid upgrade.
ACCEPTANCE: 9 scheduled entries after removal; exactly 1 Drive backup */15; all 8 unrelated cron schedules retained, incl Forgejo keepalive, mirrors, KW12.
NO_EXTRA_COST: true
SOCIAL_PUBLICATIONS: 0
