# Android emulator boot root-cause finding
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-06
RUNS: 37412271694; 37412532851; 37412351170
FINDING:
- The failing Android Agent Runtime reaches AVD creation successfully but fails at `adb wait-for-device` with exit 124.
- A dedicated diagnostic run 37412271694 captured the emulator stderr: `Unknown AVD name [diag]` and `HOME is defined but there is no file diag.ini in $HOME/.android/avd`.
- A dedicated fix probe 37412532851 passed after explicitly setting ANDROID_SDK_HOME=$HOME/.android and ANDROID_AVD_HOME=$HOME/.android/avd before AVD creation and emulator launch.
- Therefore the AVD lookup path mismatch is a proven causal defect for at least the diagnostic path. The active runtime currently still lacks those explicit exports and its latest run 37412351170 again times out at `adb wait-for-device`.

SAFE HANDOFF:
Add the same explicit ANDROID_SDK_HOME and ANDROID_AVD_HOME exports before avdmanager creation and emulator launch in android-agent-runtime.yml. Do not change unrelated login logic.
VALIDATION:
Run 37412532851 = success.
