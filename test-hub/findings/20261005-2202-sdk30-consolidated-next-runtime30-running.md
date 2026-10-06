# SDK 30-way matrix consolidated; next 30 runtime-harness variants
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN_PREVIOUS: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37400703605
RUN_NEXT: pending
SUPERSEDES: test-hub/findings/20261005-2151-agent-runtime-resume-running.md

BASELINE_PROVEN: Agent APK artifact 11384550256; validated Kwai vault; sdkmanager absolute path /usr/local/lib/android/sdk/cmdline-tools/latest/bin/sdkmanager. Previous 30-way matrix reached common ubuntu-24.04 precondition in all jobs; 17/30 variants emitted SDK_STRATEGY_PROVEN and all successful variants converged on cmdline-tools/latest/bin/sdkmanager.
FAILED_AVOIDED: bare sdkmanager PATH is retired. Runtime 37400814461 proved APK fetch and sdkmanager install progressed, then failed only because bare avdmanager was still invoked. No Agent semantic conclusion was tested.
SUCCESS_SIGNAL: next matrix variant reaches EMULATOR_BOOTED using absolute/probed avdmanager+emulator/ADB strategy, then records RUNTIME_HARNESS_PROVEN.
FAILURE_SIGNAL: variant reaches SDK tools precondition but cannot create/boot a usable AVD with its distinct strategy.
TEST_VALIDITY: proven APK retrieval + sdkmanager path + system image availability are common preconditions; variants failing before them are INVALID/NOT_TESTED.

## Consolidação dos 30 anteriores
17 variants succeeded: 2,7,8,11,12,13,16,17,20,21,22,23,24,25,28,29,30. 13 did not find an executable candidate. The causal result is one stable location, not 17 distinct implementations.

## Próxima matriz
30 variants target the next harness boundary only: avdmanager/emulator/ADB resolution and AVD boot. They do not retest deep links or authentication. The first proven boot strategy will be folded into the single Agent runtime chain.
