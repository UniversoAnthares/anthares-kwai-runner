# Independent Android boot action probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
BASELINE_PROVEN: Agent APK PROVEN; GitHub ubuntu-24.04 KVM observed; direct SDK path discovery proved sdkmanager but custom boot workflows are currently rejected/invalid before useful Agent evidence.
FAILED_AVOIDED: independent layer uses maintained reactivecircus/android-emulator-runner instead of the custom sdkmanager/avdmanager/adb orchestration; no old login/deep-link path.
SUCCESS_SIGNAL: ANDROID_BOOT_OK_API emitted after sys.boot_completed=1.
FAILURE_SIGNAL: action reaches emulator layer but cannot boot any tested API.
TEST_VALIDITY: action must start a job and reach KVM readiness; zero-job YAML rejection is INVALID.
READY: NO. AUTHENTICATED: NO. This independent probe can prove a cloud Android runtime while the 30-way custom harness is repaired.
