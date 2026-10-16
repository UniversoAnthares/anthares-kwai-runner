# Anthares Android Runtime

The runtime centralizes control of the existing Android execution surfaces behind a stable contract. The first operational backend is `MEmu_4`; future Android backends may implement the same contract without changing the publication pipeline.

## Current architecture

- `src/AntharesAndroidRuntime.psm1`: device/backend state, ADB transport, health, recovery, Kwai launch/identity signals, device lease.
- `cli/anthares-android.ps1`: stable command surface for agents and operators.
- `watchdog/anthares-android-watchdog.ps1`: bounded self-healing with exponential backoff; recovery is suppressed while an active lease exists.
- `tests/runtime-contract.tests.ps1`: source/contract checks that require the core states and safeguards.

The runtime distinguishes backend lifecycle, transport state, Android readiness and application readiness. A running `MEmuHeadless.exe` is insufficient evidence of health. A healthy MEmu backend requires the configured VM, an ADB transport in `device`, completed Android boot and a discoverable Kwai package.

## MEmu profile rule

`MEmuHyperv` resolves its media registry through the desktop owner's profile. Anthares Remote executes as SYSTEM, so the canonical profile must be loaded before every MEmu control operation:

- `USERPROFILE=C:\Users\Lucas`
- `HOMEDRIVE=C:`
- `HOMEPATH=\Users\Lucas`

Without this rule a SYSTEM process can see/start a VM without the expected registered media and produce misleading backend/ADB states.

## CLI

Examples:

```powershell
.\anthares-android.ps1 health -Pretty
.\anthares-android.ps1 recover -AllowBackendReset -Pretty
.\anthares-android.ps1 launch -Pretty
.\anthares-android.ps1 identity -Pretty
.\anthares-android.ps1 lease -Owner publisher-123 -TtlSeconds 180
.\anthares-android.ps1 release -Owner publisher-123
```

## Recovery policy

Recovery is progressive:

1. Observe the current backend and transport.
2. Start the backend when it is stopped.
3. Reconnect ADB and restart only the ADB server.
4. Reset the Android backend only when explicitly allowed by the caller/watchdog.
5. Preserve the VM disks and application data.
6. Stop escalation after the bounded recovery window and return a classified failure.

The watchdog does not reboot Windows and does not delete/recreate the MEmu VM or Kwai application data.

## Application identity

The identity probe is semantic. It requires the Kwai package in foreground plus the exact visible normalized handle `lucasrosalem` (the app may render it as `lucasrosalem` or `@lucasrosalem`) and an owner-only profile control such as `Editar perfil`/`Edit profile`. Process existence, emulator existence and package installation are supporting signals only.

## Project continuity boundary â€” 2026-10-15

The reconciled project status already closes F17-F19 on the current operational Android/mobile path. `MEmu_4` is the standby Android backend. Its remaining acceptance belongs to the final boot round with F15: automatic startup, headless/invisible execution and muted audio after a real Windows boot. The Android Runtime work therefore must not reopen F17 merely because the standby MEmu backend is degraded.

The legacy `Anthares-MEmu-Standby-Watchdog` boot action is considered superseded by this runtime design because it launches `MEmu.exe` rather than enforcing the runtime contract and its lease/backoff rules. Promotion of a replacement startup task remains part of the final boot-validation round and must preserve the current no-reboot constraint until that round is explicitly authorized.
