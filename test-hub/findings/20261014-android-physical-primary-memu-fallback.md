# Android executor — physical primary, MEmu fallback

STATUS: PARTIAL
DATE: 2026-10-14
AREA: kwai/android-executor

## Implemented
- `physical_android` is rank 1 and the only normal local Android executor.
- `memu_android` is rank 2, standby-only, and cannot be selected while the physical device is healthy.
- Failover is allowed for device/executor failures only; content/policy/platform failures do not move to MEmu.
- Circuit breaker opens after 3 consecutive device-class failures; explicit physical-device offline/unavailable may fail over immediately.
- Proven physical publisher (`kwai-up`) was promoted to `main`.
- Proven historical MEmu stack was restored under `anthares-clipper/fallback/memu/` instead of recreating it.
- `kwai_device_failover_worker.py` fences the irreversible boundary with central STARTED/COMPLETE callback argv hooks.
- Verified publication is persisted locally as `published_pending_ack` before COMPLETE; retry repairs only the acknowledgement and never republishes the job.
- Ambiguous post-click/commit outcomes remain `UNCERTAIN` and never trigger a second executor.

## Runtime rule
MEmu is permitted only as redundancy for the physical Android device. It must remain hidden/no-focus and must not become the primary executor.

## Validation pending
The Windows control tunnels are currently offline (`Anthares Remote connected=false`; WinRemote tunnel-client not seen). Therefore source integration is complete but PC deployment, actual MEmu ADB discovery, session proof, and a live failover exercise are not yet PROVEN.

## Success signal for runtime validation
1. physical probe ready + MEmu ready => router selects `physical_android`;
2. simulated/reproducible device-class degradation reaches threshold => same leased job selects `memu_android` before irreversible publish;
3. policy/content failure => no MEmu failover;
4. physical verified publication => COMPLETE ack, no MEmu activity;
5. MEmu verified failover publication => COMPLETE ack exactly once;
6. ambiguous publication => `UNCERTAIN`, no retry on either device.
