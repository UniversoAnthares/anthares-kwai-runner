# AOI7 — Hostinger mirror cron stagger without increased frequency
STATUS: RUNNING
AREA: hostinger-mirror-cron-stagger
OWNER: chatgpt-20261111
DATE_UTC: 2026-11-11T14:36Z
BASE: d3e53376aeeacddbf0088cc3c14269e8c6dc00fa
PRODUCTION: anthares.us authenticated hPanel
EVIDENCE: prior single existing cron 0,30 * * * * bash /home/u566597497/.anthares-forgejo/git-mirror-hostinger-scheduled.sh; 9 total jobs and current NPROC limit 120 temporarily. 14:30Z Forgejo Git receipt checked_utc 14:30:25.993Z, 15 repos, only anthares-kwai-runner blocked by HOSTING_PROCESS_LIMIT despite bounded 4s retry. GH public-source auth isolation fix PR #2356 merged and saved at Hostinger (editor content persisted after reload, length 9020).
HYPOTHESIS: at minutes 0 and 30, mirror overlaps Drive backup at */15, Forgejo keepalive */5, WordPress git sync */5 and minute KW12, saturating process count; new minute slots 13 and 43 avoid these coincidences and still provide exactly two mirror cycles per hour.
PLAN: replace only legacy 0,30 cron with two hourly schedules at minute 43 and minute 13, same exact script and original lock/backoff, maintaining 30-minute intervals. Add 43 first (temporary total 10 jobs), remove legacy (9), add 13 (10) and verify all unrelated 8 cron jobs unchanged. No arbitrary shell, new credentials, deletes, or changes in mirror repository refs, social posts or payments.
POSTCHECK: exact 43 * * * * and 13 * * * * schedule entries; no 0,30 mirror row; 10 crons total; backup Drive 1, keepalive 1, KW12 1, other mirror AVS 1. Fresh mirror receipt at or after next scheduled 14:43Z with 15 entries and 0 failures would prove success; no false completion if missing.
SAFETY: Owner-authed minimized isolated browser, CDP only, no mouse/keyboard physically. No Hostinger SSH executor or public HTTPS validation bypass.
