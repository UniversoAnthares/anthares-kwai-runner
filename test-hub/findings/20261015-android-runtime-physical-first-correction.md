# Anthares Android Runtime — physical-first correction and live transport evidence

STATUS: PARTIAL
AREA: android|kwai|architecture|session
DATE: 2026-10-15
RUN: none
JOB: Anthares Remote jobs 399d3a1352cd0be4, 8f3d904b10d4a0a2, 83e464c400eeb1b8
COMMIT: 7e745b6524dff300cddcc6ac925740fcb3eec57b; fbfdc08f345e4c638a151c5368eedddd24f26eb4; 96a291e2bcad0f54a7abbb32b25f6b8a39d0df66; 3fcbf4c07d81be53d88ae3525dff30ba6b59dd13
SUPERSEDES: 20261014-android-physical-primary-memu-fallback.md (architecture remains valid; this finding supersedes its pending runtime-validation state)

## Objetivo
Restore the intended Kwai executor architecture and validate the communication failure practically. Canonical priority is physical Android -> MEmu_4 automatic standby. GitHub/KVM Android remains experimental only. Anthares Android Runtime encapsulates transport discovery, supervision and recovery so a transport failure does not imply device/backend failure.

## Architectural regression identified
Commit `744d8ec5f70bef826cdae0d8dc572ea5f7798dd2` added `.github/workflows/kwai-queue-publisher-v17.yml` on `ubuntu-24.04`, enabled KVM Android and labelled it the canonical remote Android publisher while consuming the central queue. In parallel, `ci-hub/executor-routing.json` had lost the `android_execution` section expected by `tools/android_executor_router.py`.

## Corrections implemented
- `ci-hub/executor-routing.json`: physical Android restored as primary; `memu_android` restored as automatic standby; `github_android_experimental` is inactive/ineligible for normal publication.
- Remote Android v17 workflow preserved and demoted to explicit `workflow_dispatch` only, requiring the literal confirmation `EXPERIMENTAL`.
- Added `windows/android-runtime/anthares-android-runtime.ps1` as the transport/runtime layer.
- Deployed runtime copy under `C:\ProgramData\AntharesRemoteAgent\android-runtime\anthares-android-runtime-v2.ps1` through Anthares Remote.
- `windows/memu-standby/router-bridge.ps1` now calls the runtime and no longer owns a hardcoded MEmu ADB port or direct ADB path.
- TikTok routing was not changed.

## Practical evidence
### Physical Android
Canonical serial `993fce720408` was absent from `adb devices` during this validation. Runtime reported `physical_android transport=missing`. A transport recovery was attempted first and exhausted without selecting the remote Android executor.

### MEmu_4
`MEmuManage showvminfo MEmu_4 --machinereadable` proved the VM/backend independently from ADB. Observed values after recovery attempts:
- `VMState="running"`
- ADB forwarding `127.0.0.1:21543 -> 10.0.2.15:5555`
- `audio="none"`
- `MEmuHeadless.exe` running
- local TCP port `127.0.0.1:21543` listening
- `adb devices -l` still reported `127.0.0.1:21543 offline`

This is a concrete `BACKEND_RUNNING_TRANSPORT_OFFLINE` condition: backend process/VM and host forwarding are live while Android transport is unavailable.

### Recovery ladder exercised
Detached job `399d3a1352cd0be4` executed conservative MEmu transport recovery (ADB server/connect/disconnect/polling). Result: `recovery_exhausted`; backend remained running and transport remained offline.

A subsequent controlled backend recovery attempt (`8f3d904b10d4a0a2`) encountered MEmu VM state `Stopping`/lock during reset and completed without deleting VM data or clearing app data. The VM reached `poweroff`.

Detached job `83e464c400eeb1b8` then started `MEmu_4` headless. Result: backend returned to `running`; transport remained `offline`. A later ADB server recycle also left the transport offline.

Therefore the present blocker is inside the guest/ADB channel after the host-side recovery ladder, rather than absence of the MEmu backend.

### Duplicate-publication guard
Runtime selection invoked with `PublicationState=UNCERTAIN` returned:
`selected=null`, `reason=publication_state_blocks_failover`.

No publication was attempted during this validation. No uncertain result was rerouted to a second executor. Existing queue/lease/dedupe semantics remain authoritative.

## Consequence
Canonical Kwai execution order is physical Android first, MEmu_4 second. Transport recovery is mandatory before executor failover. GitHub virtual Android must not consume normal Kwai publication work and is retained only as an explicitly invoked experiment. `UNCERTAIN`, `STARTED` and `COMMITTING` states block executor switching.

F17 remains OPEN: neither the absent physical device nor the current MEmu transport state permits a fresh exact-identity proof for `@lucasrosalem`. Do not mark F17 complete until identity is proved on the intended executor and persistence after controlled restart is proved without publication.
