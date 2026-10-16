# F15 — ready for owner reboot

STATUS: READY_FOR_OWNER_REBOOT
AREA: anthares-remote | android-runtime | memu-boot
DATE: 2026-10-16

## Safety boundary

No Windows reboot, shutdown or logoff was performed in this preparation. The final reboot must be initiated manually by the owner. Automated reboot/shutdown/logoff remains prohibited.

## Anthares Remote preboot

`Anthares Remote Agent SYSTEM` is present and currently running with:
- enabled=true
- principal=SYSTEM
- RunLevel=Highest
- trigger=AtStartup (`MSFT_TaskBootTrigger`)
- action=`run-agent-system-supervisor.ps1`
- restart_count=999
- restart_interval=PT1M

`Anthares Remote Recovery Watchdog` remains disabled as required by the owner's current decision.

## Anthares Android Runtime / MEmu preboot

The installed runtime at `C:\ProgramData\AntharesRemoteAgent\android-runtime\anthares-android-runtime-v2.ps1` was synchronized with canonical repository source `windows/android-runtime/anthares-android-runtime.ps1`.

Installed SHA-256 after synchronization:
`D31210BF18192C7B0D9DF6FAFA834FBD0EFB6D2EEF52F8DC8CDF21B242CB40BF`

The stale installed implementation used to re-enable `Anthares-MEmu4-Recovery-Launcher`; canonical source no longer does that. `StartMemuOfficial` now starts `MEmu_4` directly through `MEmuManage startvm MEmu_4 --type headless`.

Canonical boot task:
- `Anthares Android Runtime MEmu SYSTEM`
- enabled=true
- principal=SYSTEM
- RunLevel=Highest
- trigger=AtStartup
- action=`C:\ProgramData\AntharesRemoteAgent\anthares-android-boot.ps1`
- restart_count=20
- restart_interval=PT2M

The wrapper is persisted in the repository as `anthares-android-runtime/watchdog/anthares-android-boot.ps1` and performs health/recovery through Anthares Android Runtime only.

All competing legacy MEmu startup authorities are disabled:
- `Anthares MEmu4 Headless Boot`
- `Anthares-MEmu4-Boot`
- `Anthares-MEmu-Standby-Watchdog`
- `Anthares-MEmu4-Recovery-Launcher`

MEmu audio configuration is already:
- `audio=none`
- `audio_out=off`
- `audio_in=off`

## Related phase state

Current finding `20261016-f17-f20-final-revalidation.md` closes F17–F20 on current evidence. F8 remains superseded by the exclusive Anthares Remote policy and must not revive WinRemote/MeshCentral.

## Remaining acceptance

F15 is not yet fully PROVEN because its acceptance requires one real owner-initiated Windows reboot. After the owner reports that Windows is back, verify without causing another reboot:
1. Anthares Remote reconnects through Vercel+Neon.
2. `Anthares Remote Agent SYSTEM` started from the boot trigger and Remote command execution works.
3. `Anthares Remote Recovery Watchdog` remains disabled.
4. `Anthares Android Runtime MEmu SYSTEM` ran automatically.
5. `MEmu_4` is started headless/invisible and audio remains disabled.
6. Anthares Android Runtime health/recovery result is recorded; any standby transport degradation is reported separately rather than triggering a Windows reboot.

Only after those post-boot observations should F15 be marked PROVEN.