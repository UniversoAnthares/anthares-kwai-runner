# Exact owner verification via authenticated menu state/settings
STATUS: RUNNING
AREA: kwai-existing-tab-owner-helper
DATE: 2026-10-09
RUN: none
JOB: none
COMMIT: 7f6c0dab649498f55c20559e50e66bdef145d77e
SUPERSEDES: none
BASELINE_PROVEN: live ownerStateLive20261009_1844 proves authenticated_ui_detected=true but menu href/text/navigation and hydrated owner-state all remain false.
FAILED_AVOIDED: do not repeat public-profile Edit profile, generic account-row, named Profile/Perfil, or generic hydration-state paths unchanged.
SUCCESS_SIGNAL: exact expected handle is bound to the authenticated account menu through bounded React menu state OR reached through a safe Settings/Account/Profile control from that authenticated menu; live owner_probe returns identity_verified=true.
FAILURE_SIGNAL: both bounded React-menu evidence and authenticated settings/account navigation fail to bind the exact handle; identity remains false.
TEST_VALIDITY: CI only validates syntax/security. Only live Codespaces owner_probe is identity proof. No cookies/storage/tokens/raw page text/screenshots are exported and no publication is attempted.
