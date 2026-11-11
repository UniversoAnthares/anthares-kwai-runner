# AOI7 — Hostinger staggered Git mirror cron: PROVEN 15/15
STATUS: PROVEN_MIRROR_SYNC_PARTIAL_HOSTING_CAPACITY
OWNER: chatgpt-20261111
DATE_UTC: 2026-11-11T14:49Z
BASE: d3e53376aeeacddbf0088cc3c14269e8c6dc00fa
LEASE: CLOSED
PREVIOUS_LEASE: 20261111-hostinger-mirror-cron-stagger-lease.md

## Production changes / receipts
- Hostinger hPanel Cron Jobs on anthares.us originally had exactly one `0,30 * * * * bash /home/u566597497/.anthares-forgejo/git-mirror-hostinger-scheduled.sh`.
- Introduced `43 * * * *` with the identical script via hPanel. Deleted the old `0,30` cron after preserving the new one, then introduced `13 * * * *` with identical script.
- Production readback hPanel: 10 scheduled cron jobs; exactly `43 * * * *` and `13 * * * *` for mirror, zero `0,30`; Forgejo keepalive=1, Drive backup=1, KW12=1, AVS mirror=1 unchanged.
- New `43` job completed in production (Hostinger Cron Jobs > Ver resultado):
  `HOSTINGER_MAIN_SYNC=RUNNING 2026-11-11T14:43:01Z`
  `anthares-kwai-runner SYNCED_FAST_FORWARD_VERIFIED`
  `HOSTINGER_GIT_SYNC=VERIFIED covered= 15 blocked= 0`
  `HOSTINGER_MAIN_SYNC=OK`
- All the other 14 statuses were validated (source-ref verified or empty source match). Full parity recovered after failed 14:00 and 14:30 cycles.
- Existing GitHub PR #2356 `d3e53376` applied to production public-source GitHub authentication; Python file live SHA=56d10aa8cafab9afa2ec9dacbff839da5ae64d07, confirmed after browser reload (9020 chars). New scripts no force, no prune, no credential changes for private mirrors.
- No checkout/push/force/delete of Git refs, no SSH/Hostinger external executor, no new paid plan, no public social publication, no kill or global stop; CDP browser minimized isolated.

## Remaining external constraints
- At 14:43Z hPanel Resource Usage recorded 82 processes (above the ORIGINAL Premium quota of 80) and 83 at 14:44Z, 92 at 14:45Z. The FREE 24h boost to 120 is active and expires approximately 2026-11-12T12:09Z. Therefore success under boosted cap does not prove sustainability under original cap.
- The Forgejo keepalive cron output remained empty after code deployment; original Forgejo log at 13:30Z showed daemon/socket activity. No fresh keepalive success receipt attested by this cron step.
- External public Forgejo HTTPS verification was blocked in a prior security-gated session and must not be rerouted through other channels.
- Overall AOI7: mirror parity and schedule verified, resource limit/keepalive and HTTPS gate remain PARTIAL.
