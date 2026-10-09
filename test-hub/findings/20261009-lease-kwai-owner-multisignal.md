# Lease: multi-signal exact owner verification
STATUS: RUNNING
AREA: kwai-existing-tab-owner-helper
DATE: 2026-10-09
OWNER: chatgpt-owner-multisignal
LEASE_UNTIL: 2026-10-09T19:20:00Z
HEAD_BASELINE: 5390a67e022eabd3fdae3479ea15b4ba8ceb571d
RESOURCES: .devcontainer/kwai-existing-tab-owner.py
BASELINE_PROVEN: live profile_check proves signed-in UI via logout_visible=true; owner_probe is a false negative because its avatar selector/menu parser is narrower than the proven identity guard.
FAILED_AVOIDED: do not infer ownership from logout alone, public profile content, or display name; do not export cookies/tokens/page text; do not publish as a test.
SUCCESS_SIGNAL: safe top-right account menu opens and exact expected handle is proved by a boolean-only menu href/text match or exact own-profile navigation from that authenticated menu.
FAILURE_SIGNAL: exact handle evidence absent => identity_verified=false.
TEST_VALIDITY: CI validates code only; live Codespace owner_probe is required.
PEER: GitLab project 87307248 has no matching helper file (404); no blind mirror.
