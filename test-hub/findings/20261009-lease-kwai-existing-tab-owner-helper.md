# Lease: independent existing-tab Kwai owner identity probe
STATUS: RUNNING
AREA: kwai-existing-tab-owner-helper
DATE: 2026-10-09
OWNER: chatgpt-existing-tab-owner-helper
LEASE_UNTIL: 2026-10-09T18:20:00Z
HEAD_BASELINE: 725711c7adf226fd2f68a2fb49d99c430067b33e
RESOURCES: .devcontainer/kwai-existing-tab-owner.py (new file only)
BASELINE_PROVEN: issue #12 authenticated_ui_detected=true and logout_visible=true, while identity_verified=false; Chrome CDP is live.
FAILED_AVOIDED: public profile probe requiring Edit profile; no navigation, no cookies, no storage, no screenshot or page text export.
SUCCESS_SIGNAL: independent helper checks existing authenticated Kwai tab and exact owner handle only from visible account menu/profile controls; returns boolean-only evidence; no false positive from public profile link alone.
FAILURE_SIGNAL: exact owner link absent or login gate visible yields identity_verified=false.
TEST_VALIDITY: helper static checks are not live identity proof; integration requires separate bridge lease and live result.
PEER: GitLab project 87307248 target helper path 404; no blind mirror.
