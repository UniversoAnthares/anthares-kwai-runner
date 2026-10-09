# Kwai profile navigation fallback and safe bridge refresh QA
STATUS: PARTIAL
AREA: kwai-codespaces-browser-identity
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37959883736
JOB: browser-only-security
COMMIT: 154ea4c9720ba2ebdca055204a51f0e333a2807d
SUPERSEDES: 20261009-kwai-independent-profile-navigation-implemented.md

BASELINE_PROVEN: Issue #12 real command independent20261009_1630a returned status=ok, chrome_connected=true, account_menu_open_attempted=true, independent_profile_navigation_attempted=false, identity_verified=false.
FAILED_AVOIDED: original fallback selected only one avatar image and did not recognize explicit Profile links/menu items. New fallback prioritizes explicit Profile/Perfil menu actions and /@ links in a constrained top-right dropdown, then avatar-row fallback. It records sanitized flags profile_menu_found/profile_candidate_found/profile_navigation_reached; never outputs DOM or credentials.
ADDITIONAL: owner-only issue command refresh_bridge fast-forwards origin/main and restarts bridge through .devcontainer/kwai-start.sh, without restarting Chrome or touching private profile.
SUCCESS_SIGNAL: after one Codespace update, fresh issue #12 profile_check reports profile_navigation_reached=true and identity_verified=true only if exact handle and owner controls match. Refresh_bridge command reports refresh_started=true.
FAILURE_SIGNAL: no menu or profile candidate, no navigation, wrong handle or missing owner control.
TEST_VALIDITY: hosted security QA run 37959883736 SUCCESS for commit 154ea4c972, synthetic/static only; live Codespace still needs to load commit before live test. No publication/session export authorized.
