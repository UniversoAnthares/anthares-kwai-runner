# Lease Codespaces bridge startup/refresh hardening
STATUS: RUNNING
AREA: kwai-codespaces-bridge-startup
DATE: 2026-10-09
OWNER: chatgpt-bridge-startup-refresh
LEASE_UNTIL: 2026-10-09T16:40:00Z
HEAD_BASELINE: ed68823aa127e96c0de299e20d75b64c9f35cf9f
RESOURCES: .devcontainer/kwai-start.sh, new bridge supervisor/startup support only
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: issue #12 already proved the persistent Codespaces Chrome/CDP bridge can inspect/open_home successfully; commit 8074f570f08c368a295fec21c3e77f28ec03dcb5 passed strict private profile-check QA, but the live bridge process still serves the older result schema until refreshed.
FAILED_AVOIDED: do not retry failed Android/Google login runs 37953770576/37954011611; do not modify .devcontainer/kwai-command-bridge.py or issue #12 while the existing kwai-codespaces-command-bridge lease remains active; do not reset Chrome, browser profile, cookies, credentials, or session state.
SUCCESS_SIGNAL: Codespace startup becomes idempotently responsible for starting the command bridge from the current checkout, with PID verification and without restarting Chrome; future Codespace start/resume can load current bridge code automatically.
FAILURE_SIGNAL: startup patch can terminate/recreate Chrome or its profile, launches duplicate bridges, or cannot safely distinguish the bridge PID.
TEST_VALIDITY: shell/static QA must prove syntax, PID ownership checks and explicit absence of Chrome/profile destructive operations; this patch alone is not live identity or publication proof until the running Codespace reloads it.
SECURITY: no secrets, cookies, tokens, credentials, page text or browser-state export.
