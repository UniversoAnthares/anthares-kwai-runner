# Lease — Codespaces create/upload surface probe
STATUS: RUNNING
AREA: kwai-codespaces-create-surface-probe
DATE: 2026-10-09
OWNER: chatgpt-create-surface-probe
LEASE_UNTIL: 2026-10-09T16:59:00Z
HEAD_BASELINE: e1934536ecb39d02158721cde346859533a16d81
RESOURCES: .devcontainer/kwai-create-surface-probe.py, tests/test_kwai_create_surface_probe.py, .github/workflows/kwai-create-surface-probe-qa.yml
BASELINE_PROVEN: browser-only Codespaces bridge is alive; existing-tab auth/profile work is under a separate lease and its hosted QA passed. This lease intentionally avoids .devcontainer/kwai-command-bridge.py, .devcontainer/kwai-identity-guard.py, tests/test_kwai_codespaces_browser.py and issue #12.
FAILED_AVOIDED: no Android, no new browser/profile, no storage/cookie/session export, no logout, no screenshot, no live publish side effect.
SUCCESS_SIGNAL: offline hosted QA proves a helper can classify existing Kwai/Studio pages into login-gate/create-upload-ready sanitized booleans without launching a browser or reading session material.
FAILURE_SIGNAL: helper requires new profile/browser state, leaks page/session data, clicks/publishes, or QA fails.
TEST_VALIDITY: synthetic DOM/classification QA only; it does not prove the live Kwai account or publication readiness until later integrated into the already-running Codespaces browser.
