# Live existing-tab create/upload surface integration
STATUS: RUNNING
AREA: kwai-codespaces-browser-create-surface-integration
DATE: 2026-10-09
OWNER: chatgpt-kwai-profile-navigation
LEASE_UNTIL: 2026-10-09T18:00:00Z
HEAD_BASELINE: 3090337b6097e5d07292a5312abb2d7bd2aaf308
RESOURCES: .devcontainer/kwai-command-bridge.py (allowlisted read-only command only)
BASELINE_PROVEN: existing GitHub issue #12 bridge commands reach private Codespaces Chrome; authenticated_ui_detected=true and logout_visible=true. Offline classifier test 37959630521 passed.
FAILED_AVOIDED: no Android, no PC, no new Chrome profile, no session export, no login/logout, no upload or publication. No repetition of failed DOM-click navigation.
SUCCESS_SIGNAL: owner command create_probe returns status=ok and sanitized operational_create_surface/read_only_probe flags from the existing Kwai tab, with no Chrome/profile mutation.
FAILURE_SIGNAL: no live bridge response, Chrome unavailable, or unexpected mutation.
TEST_VALIDITY: live create-surface visibility is distinct from exact account identity; no publication is authorized without both independent proofs.
PEER: GitLab 87307248 main lacks the target bridge file (404), so no blind mirroring.
