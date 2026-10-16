# F15 + MEmu4 post-boot reconciliation — 2026-10-16

STATUS: CURRENT

## User safety rule
Never reboot, shut down, or log off the Windows PC automatically. Ask the user to do it manually when a real reboot/logoff proof is required.

## Boot evidence
Windows Event Log shows three fresh service-start/boot events on 2026-10-16 before this audit (15:39:55Z, 15:47:21Z, 15:59:01Z). The current OS boot is 2026-10-16T15:58:24.5Z.

The canonical task `Anthares Remote Agent SYSTEM` is enabled, Running, runs as SYSTEM, and last started at 15:59:59Z after the current boot. The supervisor state reports identity `NT AUTHORITY\\SYSTEM`, Session 0, and the only canonical remote agent process is `anthares-remote-agent-v4-c8.exe` in Session 0. `Anthares Remote Agent User` is disabled. `Anthares Remote Recovery Watchdog` is disabled. This is sufficient to close the real-boot portion of F15. A real user-logoff proof is still separate if retained as an acceptance criterion.

## MEmu4 reconciliation
A later agent had re-enabled `Anthares-MEmu4-Interactive-Launcher` and disabled the canonical `Anthares MEmu4 Headless Boot`. This was corrected during the audit:
- `Anthares MEmu4 Headless Boot` is enabled and its latest run completed with result 0.
- `Anthares-MEmu4-Interactive-Launcher`, `Interactive-Launch-Once`, `Interactive-Memuc-Launcher`, `NativeStart-*`, legacy `Anthares-MEmu4-Boot`, `Recover`, and standby-watchdog launch paths are disabled.
- The Android runtime `StartMemuOfficial` was changed so it starts the canonical `Anthares MEmu4 Headless Boot` task instead of re-enabling the interactive launcher.
- The runtime source parses successfully after the reconciliation.

MEmu 9 currently needs a background bootstrap helper to make the guest and ADB transport healthy. That helper can leave a `MEmu.exe` process, but the relevant acceptance criterion is no visible window, not the mere absence of that process. Current process inspection showed `MainWindowHandle=0` / empty title for both MEmu and MEmuHeadless. Audio is persistently disabled (`audio=none`, `audio_out=off`, `audio_in=off`). Runtime health reports `127.0.0.1:21543` as `device`, boot completed, `com.kwai.video` installed, and MEmu healthy. Do not kill the background bootstrap process merely to obtain a one-process aesthetic state if doing so also kills the healthy headless backend.

`MEmuManage showvminfo` can still report stale `VMState=aborted`; the Anthares Android Runtime reconciles this against a live `MEmuHeadless.exe` and correctly reports backend running. Treat the runtime's reconciled state plus ADB/guest proof as authoritative for this known MEmuManager inconsistency.

## Executor policy
Current runtime policy remains: physical Android first, MEmu Android second, remote Android experimental only. The physical device was not attached to this PC's ADB during this audit; that is not evidence that the user-confirmed physical/mobile publication path is invalid. Do not reopen F17-F19 solely because the phone is temporarily absent from local ADB.

## Remaining acceptance
- F15 boot persistence: CLOSED by real boot evidence.
- F15 logoff independence: still pending only if the project retains real logoff as a mandatory acceptance test. Never initiate logoff automatically; ask the user.
- MEmu4 post-boot invisibility/mute/health: current runtime state is healthy/invisible/muted after the user's reboots; one more reboot is not required merely to repeat already-observed boot behavior unless a later change invalidates it.
- F17-F22 remain closed under the reconciled status finding unless newer project evidence explicitly supersedes them.
