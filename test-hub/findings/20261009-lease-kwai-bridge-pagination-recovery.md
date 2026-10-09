# Lease: recover Codespaces bridge after issue #12 exceeded first comment page
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-09
OWNER: chatgpt-bridge-pagination-recovery
LEASE_UNTIL: 2026-10-09T17:50:00Z
RESOURCES: .devcontainer/kwai-command-bridge-v2.py, .devcontainer/kwai-start.sh
BASELINE_PROVEN: live issue #12 has more than 100 comments; page=2 contains commands after mobile_cdp_probe. Existing bridge polls only comments?per_page=100, so newer commands are invisible.
FAILED_AVOIDED: do not repeat issue commands against a bridge that cannot see page 2; do not restart Chrome or touch its profile; do not use Android or export session data.
SUCCESS_SIGNAL: bridge v2 polls newest comments, starts without touching Chrome/profile, responds to owner_probe/profile_check/create_probe commands posted after the 100-comment boundary.
FAILURE_SIGNAL: bridge cannot start, cannot see newest owner command, or any Chrome/profile mutation occurs.
TEST_VALIDITY: owner-only issue command response from Codespaces is required; repository commit/CI alone does not prove live activation.
PEER: GitLab project 87307248 does not contain .devcontainer/kwai-identity-guard.py (404), so no blind mirroring.
