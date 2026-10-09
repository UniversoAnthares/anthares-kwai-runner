# Live Codespaces studio read-only navigation probe
STATUS: RUNNING
AREA: kwai-codespaces-browser-studio-probe
DATE: 2026-10-09
OWNER: chatgpt-kwai-profile-navigation
LEASE_UNTIL: 2026-10-09T18:00:00Z
HEAD_BASELINE: 9e7e7f1b0811125e6d996220beaf6c58403eca41
RESOURCES: .devcontainer/kwai-command-bridge.py
BASELINE_PROVEN: live issue #12 createProbeLive20261009a: authenticated browser tab present, login_gate_visible=false, operational_create_surface=false, studio_tab_present=false; existing-tab read-only classifier works.
FAILED_AVOIDED: no Android, PC executor, Chrome profile replacement, cookie/session export, upload or publish; do not confuse normal Kwai homepage with Studio create surface.
SUCCESS_SIGNAL: a temporary tab to fixed https://studio.kwai.com/ is classified read-only with sanitized studio_tab_present/login_gate_visible/create controls, and closed without changing original tab.
FAILURE_SIGNAL: command unavailable, navigation fails, or existing tab/session modified.
TEST_VALIDITY: temporary Studio UI is a diagnostic, not proof of account identity or publication.
PEER: GitLab main lacks bridge path; do not mirror blindly.
