# Lease: repair Kwai native login selectors using captured Android XML
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-10
OWNER: chatgpt-qa-handoff-1859Z
LEASE_UNTIL: 2026-10-10T19:23:34Z
HEAD_BASELINE: 8b1c8d09e7ba939757ed8bdea4540ad6909bd45b
RESOURCES: kwai_remote_android_login.sh, tools/kwai_login_ui_locator.py, tests/test_kwai_login_ui_locator.py
BASELINE_PROVEN: run 38062865655 artifact 11674185542 contains authentic Android UI XML with native login sheet, Continue with Google button and 'or use Facebook | Phone | Email' entry, but no EditText. Issue #19 reports false no-login and 12-minute timeout.
FAILED_AVOIDED: do not repeat blind Google taps or 24 attempts; do not claim login from a text label alone; no Android rerun until selector correction is validated on real XML; no publication, session reset or credentials.
SUCCESS_SIGNAL: selector distinguishes native method chooser from actual EditText login form; identifies Email sub-action within chooser; deterministic unit tests from real redacted XML and fast GitHub check pass; script exits promptly when no login form.
FAILURE_SIGNAL: false-positive email form, wrong Email segment tap, regression to 24 blind Google attempts, or syntax failure.
TEST_VALIDITY: static selector proof does not imply authenticated account or persistent session; Android real login requires separate authorized run and independent identity proof.
SUPERSEDES: 20261010-0301-lease-kwai-auth-private-persistence.md
