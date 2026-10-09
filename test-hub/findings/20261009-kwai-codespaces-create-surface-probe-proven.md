# Codespaces existing-tab create/upload surface probe
STATUS: PROVEN
AREA: kwai-codespaces-create-surface-probe
DATE: 2026-10-09
RUN: 37959630521
JOB: 113918854916
COMMIT: dde6535398d7d3abba6ab4a9e9ee2d0e1c56c052
SUPERSEDES: 20261009-lease-kwai-codespaces-create-surface-probe.md

BASELINE_PROVEN: browser-only Codespaces bridge/session path remains the preferred executor; this change is isolated from the active existing-tab auth/profile lease.
FAILED_AVOIDED: no Android, no new browser/profile, no session/cookie/storage export, no screenshot, no click, no upload, no publication side effect.
SUCCESS_SIGNAL: hosted job 113918854916 executed six focused tests and all passed, including operational create surface without login gate, file-input readiness, fail-closed login/no-tab cases, boolean-only public contract, and source-level prohibition of browser launch/session export/mutating actions.
FAILURE_SIGNAL: none observed in the declared offline QA scope.
TEST_VALIDITY: PROVEN only for the helper/classification contract and safety properties. This does not claim the live account is authenticated, exact identity is verified, or live create/upload controls are present until the helper is integrated into the already-running Codespaces browser and a sanitized live result is obtained.
NEXT: after the separate command-bridge/auth lease releases, integrate this helper into the existing live bridge, refresh bridge only without touching Chrome/profile, then require operational_create_surface=true together with exact identity proof before any real upload/publish action.
