# F15 preboot preflight — 2026-10-16

STATUS: PARTIAL / PREBOOT READY IN SOURCE
AREA: Anthares Remote boot persistence + MEmu4 boot acceptance
DATE: 2026-10-16

## Source-level prerequisites verified

- `anthares-remote-agent/windows/repair-system-startup-task.ps1` exists and independently registers `Anthares Remote Agent SYSTEM` as SYSTEM / Highest / AtStartup, with restart count 999, one-minute restart interval, StartWhenAvailable and IgnoreNew.
- The same repair script explicitly stops/disables `Anthares Remote Recovery Watchdog`; the watchdog must remain disabled by current owner policy.
- Therefore F15 does not require reintroducing the old watchdog.
- MEmu_4 source/runtime evidence confirms canonical forwarding `127.0.0.1:21543`, audio `none`, `audio_out=off`, `audio_in=off`, and a valid headless start path via `MEmuManage.exe startvm MEmu_4 --type headless` under the canonical Lucas profile.

## Live evidence / blocker

- Anthares Remote was connected through Vercel+Neon during this preflight.
- Direct task-state audit was queued because Anthares Remote was under heavy concurrent use by active Kwai leases; no extra mutation was added.
- Historical private-queue issue `UniversoAnthares/anthares-ara-queue#133` is closed with no result comments and must NOT be treated as proof that the SYSTEM startup task was installed.
- Current live proof of `Anthares Remote Agent SYSTEM` task presence/enabled/principal/trigger remains required before reboot.
- MEmu_4 transport is concurrently leased to another agent for ADB single-daemon repair; this preflight deliberately did not interfere.

## Final acceptance still required

Do not close F15 until one real reboot proves all of the following:
1. Anthares Remote reconnects without user logon/manual action through the canonical SYSTEM startup task.
2. `Anthares Remote Recovery Watchdog` remains disabled.
3. Exactly one canonical Anthares Remote executor is active.
4. MEmu_4 starts automatically using the managed standby/runtime path, headless/invisible and muted.
5. Post-boot Anthares Remote command execution succeeds.

No reboot was performed in this preflight.