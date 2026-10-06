# ADB 30-way workflow rejected before jobs; corrected matrix staged
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
SUPERSEDES: test-hub/findings/20261005-2213-runtime30-invalid-next-adb30-running.md
BASELINE_PROVEN: Agent APK artifact PROVEN; sdkmanager, avdmanager and emulator absolute paths PROVEN/observed executable; Android 35 x86_64 image installation reaches completion.
FAILED_AVOIDED: runs 37402947266 through 37403085975 of android-adb-boot-30 produced zero jobs, so they are workflow-definition INVALID and provide no ADB/boot evidence. The new matrix removes the YAML/inline expression constructs responsible for pre-job rejection and uses one fixed proven absolute toolchain with only boot-parameter variants.
SUCCESS_SIGNAL: each valid job emits TEST_VALIDITY=TOOLS_AND_IMAGE_READY; any job that boots emits RUNTIME_HARNESS_PROVEN=<variant>.
FAILURE_SIGNAL: after common tools/image precondition, emulator/ADB fails to reach sys.boot_completed for a specific boot strategy.
TEST_VALIDITY: zero-job workflow rejection is INVALID; a variant counts only after TEST_VALIDITY marker.

READY: NO. AUTHENTICATED: NO. Current position: runtime harness before Agent installation/Accessibility validation.
