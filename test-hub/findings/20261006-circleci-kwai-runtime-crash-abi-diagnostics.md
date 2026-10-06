# CircleCI Kwai runtime crash/ABI diagnostic layer
STATUS: READY
AREA: kwai
DATE: 2026-10-06
COMMIT: b44847ee8a1186cbc3161fcaa0d30da2cb4b9aa6
SUPERSEDES: none

## Objective
When the post-install Kwai runtime probe cannot obtain a process/UI, preserve the evidence needed to distinguish package absence, stopped/disabled package, launch routing failure, Java crash, native/ABI crash, native-bridge failure, or dynamic-loader failure.

## Added evidence
On FAILURE_SIGNAL=KWAI_RUNTIME_OR_UI_NOT_READY the CircleCI job now records pm path, selected package metadata including primary/secondary ABI and stopped/enabled state, top/resumed activities, and a bounded filtered logcat window for AndroidRuntime, FATAL EXCEPTION, com.kwai.video, UnsatisfiedLinkError, SIGSEGV/SIGABRT, native bridge and dlopen failures.

## Rule
Do not change APK splits or authentication routes until this diagnostic evidence identifies a causal class.