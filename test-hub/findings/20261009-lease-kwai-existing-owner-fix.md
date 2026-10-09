# Lease: repair existing-tab owner probe false negative
STATUS: RUNNING
AREA: kwai-existing-tab-owner-helper
DATE: 2026-10-09
OWNER: chatgpt-existing-tab-owner-fix
LEASE_UNTIL: 2026-10-09T18:55:00Z
HEAD_BASELINE: fcc2abbf80ba4783618f0be7fb9a96129106e649
RESOURCES: .devcontainer/kwai-existing-tab-owner.py
BASELINE_PROVEN: live issue #12 profile_check reports authenticated_ui_detected=true, logout_visible=true; owner_probe reports authenticated_ui_detected=false because it only checks menu controls already open.
FAILED_AVOIDED: do not infer account identity from logout alone; do not navigate existing tab or expose session.
SUCCESS_SIGNAL: safe top-right avatar menu activation followed by exact own-profile link verification and live identity result.
FAILURE_SIGNAL: missing owner link remains fail-closed.
TEST_VALIDITY: CI does not prove identity; live result needed.
PEER: GitLab helper path absent; no mirror.
