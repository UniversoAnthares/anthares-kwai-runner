# Official Android emulator package unavailable on GitHub ARM64 runner
STATUS: PROVEN_FAILED_ROUTE
AREA: kwai-arm64-runtime
DATE: 2026-10-12
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38332528937
JOB: 115085265292

## Evidence
The `ubuntu-24.04-arm` hosted runner is native `aarch64`, but Android `sdkmanager --install emulator ...` returns `Warning: Failed to find package 'emulator'`. No `$ANDROID_HOME/emulator/emulator` binary is installed; version probe exits 127.

Signal: `ARM64_OFFICIAL_EMULATOR_NATIVE=UNAVAILABLE`.

## Consequence
Do not spend more rounds trying to invoke the official Android emulator natively on this ARM hosted runner. Continue with QEMU plus reproduction of the Android emulator first-stage topology, or move to a provider that supplies a supported Android emulator substrate.
