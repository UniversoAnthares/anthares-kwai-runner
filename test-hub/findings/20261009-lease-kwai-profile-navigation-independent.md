# Lease: own-profile navigation without logout-menu dependency
STATUS: RUNNING
AREA: kwai-codespaces-browser-identity
DATE: 2026-10-09
OWNER: chatgpt-kwai-profile-navigation
HEAD_BASELINE: 1f967f3fc25f506f2bb7824710c667ebf681d32f
LEASE_UNTIL: 2026-10-09T17:05:00Z
RESOURCES: .devcontainer/kwai-identity-guard.py, .devcontainer/kwai-command-bridge.py
BASELINE_PROVEN: GitHub issue #12 remote CDP commands execute; latest profile_check has account_menu_open_attempted=true but logout_visible=false.
FAILED_AVOIDED: do not gate own-profile navigation on logout visibility. Use a disposable Kwai tab and header avatar/account row, then compare navigated URL to exact expected handle. Keep account ownership fail-closed.
SUCCESS_SIGNAL: live Codespaces issue #12 reports own-profile navigation attempted and exact-match identity only if independent owner evidence exists.
FAILURE_SIGNAL: profile navigation not reached or wrong handle.
TEST_VALIDITY: code changes and offline syntax checks do not establish live login; only new issue #12 response after Codespace refresh does.
