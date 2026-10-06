# Interactive Kwai runtime — second causal repair after 40-way QA
STATUS: RUNNING
DATE: 2026-10-06
AREA: kwai-login

RESULT OF 37497733323:
- SDK installation completed; emulator package and Android 35 image were installed.
- Failure moved to adb wait-for-device: exit 124.
- No useful emulator diagnostics were printed because the timeout exited the shell before the log dump.
- This proves the previous SDK discovery defect is fixed and the remaining defect is emulator boot/runtime configuration.

40-way QA:
- Workflow 37497795014 launched the requested 40-case discovery matrix. The GitHub jobs endpoint exposes the first 30 jobs per page; observed cases included both positive and negative environment assertions. These are diagnostic probes, not publication tests.
- Do not interpret expected failures of command-PATH probes as production failures.

CAUSAL REPAIR:
- Aligned the interactive workflow with the already PROVEN android-agent-runtime configuration:
  - Enable /dev/kvm.
  - ANDROID_SDK_HOME=$HOME during SDK/AVD creation.
  - ANDROID_AVD_HOME=$HOME/.android/avd.
  - -no-snapshot -wipe-data -accel on -cores 2.
  - bounded 120s adb wait with emulator log, /dev/kvm and emulator-version diagnostics.
  - bounded 300s boot-completion wait.

NEW COMMIT:
b32dc38de70780a400c0d08d998c4dc5635deabe

NEXT:
- Fresh run from this commit must reach EMULATOR_BOOTED.
- Then proceed through vault installation and legitimate interactive owner login.
- Real publication remains fenced behind authenticated READY.
