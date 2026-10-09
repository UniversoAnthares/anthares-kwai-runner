# Repair Kwai Codespaces guard: auto-open account menu for read-only verification
STATUS: RUNNING
AREA: kwai-codespaces-browser-identity
DATE: 2026-10-09
OWNER: chatgpt-kwai-codespaces-menu-auto-open
LEASE_UNTIL: 1791559269
HEAD_BASELINE: 27cbb0a82add8be6980bae1d347e09b44c68970a
RESOURCES: .devcontainer/kwai-identity-guard.py, tests/test_kwai_codespaces_browser.py, .github/workflows/kwai-codespaces-browser-smoke.yml
BASELINE_PROVEN: 37943856012 Chrome DOM synthetic menu tests passed; 37944151232 security QA 12/12; screenshot of real Codespace private guard shows chrome_connected=true but authenticated_ui_detected=false, account_menu_logout_visible=false because menu is closed when verification starts. User screenshot earlier showed actual signed-in Kwai menu 'Lucas Rosalem' and 'Log out'.
FAILED_AVOIDED: read-only passive DOM check while account menu is closed; do not require user to hold menu open. Do not infer exact @universo.anthares from display name, profile public URL or absent login button. Do not touch user Chrome profile/session, no Android, no PC executor.
SUCCESS_SIGNAL: inspector opens avatar menu automatically in a disposable tab, observes visible Log out, separates authenticated UI from exact account handle, never clicks Log out, never exports cookies; hosted Chrome synthetic tests and security QA pass.
FAILURE_SIGNAL: wrong account verified, signed-out UI reported signed-in, unsafe click or session export, Chrome killed, test precondition not reached.
TEST_VALIDITY: hosted Chrome DOM tests synthetic, cannot prove real account ownership; live Codespace private 8765 check needed after safe guard refresh.
PEER_CHECK: GitLab same file returned 404 on main, mirror behind; do not blindly sync.
CONCURRENCY: previous Codespaces identity-menu lease closed by PROVEN finding; distinct from Android login and publishing leases.
