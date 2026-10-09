# Lease: browser mobile-client emulation (independent layer)
STATUS: RUNNING
AREA: kwai-codespaces-browser-mobile-cdp
DATE: 2026-10-09
OWNER: chatgpt-kwai-mobile-cdp
LEASE_UNTIL: 2026-10-09T19:00:00Z
HEAD_BASELINE: 318b816913635be64f4d02567d7ce0e949128530
RESOURCES: .devcontainer/kwai-mobile-cdp-probe.py (new), .devcontainer/kwai-command-bridge.py (allowlist only)
BASELINE_PROVEN: Issue #12 authentic Kwai web UI (logout visible) but Studio presents login gate. Existing mobile probe changes only viewport and may report a false-positive create control without file input. CDP bridge and private Chrome session are working.
FAILED_AVOIDED: no Android emulator, no PC executor, no cookie/session export, no fake claim of native mobile app, no change to existing Chrome tabs, no upload/publish. Different causal mechanism from viewport-only test: per-target CDP mobile UA + client hints + touch + device metrics.
SUCCESS_SIGNAL: owner issue #12 mobile_cdp_probe returns real mobile runtime signals and whether an actionable input[type=file] exists without login wall, from disposable tab; original tabs unaffected.
FAILURE_SIGNAL: mobile CDP fails, login wall remains, or upload UI still absent; report PARTIAL/FAILED not production-ready.
TEST_VALIDITY: mobile web emulation is NOT native Android app identity. Never treat CSS create button alone as publishing capability. Hosted QA is syntax/static only; live bridge is required.
PEER: GitLab project 87307248 main .devcontainer/kwai-command-bridge.py is absent (404); no blind mirroring.
PARALLELISM: queued hosted browser-security/create-surface QA tests cover separate existing viewport classifier; this is independent per-target CDP mobile-client experiment, no competing run.
