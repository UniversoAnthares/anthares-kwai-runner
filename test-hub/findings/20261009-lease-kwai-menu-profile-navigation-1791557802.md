# Kwai Codespaces exact account handle via read-only own-profile navigation
STATUS: RUNNING
AREA: kwai-codespaces-browser-identity
DATE: 2026-10-09
OWNER: chatgpt-kwai-codespaces-menu-profile-navigation
LEASE_UNTIL: 1791559002
HEAD_BASELINE: d17dc38199075a20ad08f06004cbb9dd7a9cc75f
RESOURCES: .devcontainer/kwai-identity-guard.py, .github/workflows/kwai-codespaces-browser-smoke.yml, tests/test_kwai_codespaces_browser.py
BASELINE_PROVEN: 37947690214 Chrome synthetic menu auto-open works and rejects wrong handle; 37947544588 security QA 13/13. Real Codespace menu shows Lucas Rosalem + Log out but may not have a direct href to @universo.anthares.
FAILED_AVOIDED: expecting exact @handle as text or href in account menu; display name alone cannot prove ownership; public profile URL alone cannot prove ownership.
SUCCESS_SIGNAL: inspector clicks ONLY visible account profile avatar inside authenticated dropdown of disposable page, observes resulting own-profile URL equals expected handle; rejects wrong or missing handle; no logout, credentials, cookies or user-tab navigation.
FAILURE_SIGNAL: any click on logout or unrelated feed item, false-positive identity for wrong handle, session exported, test precondition not reached.
TEST_VALIDITY: hosted synthetic Chrome DOM only; live Codespace verification still required.
PEER_CHECK: GitLab .devcontainer/kwai-identity-guard.py main returned 404; no mirror.
CONCURRENCY: prior Codespaces identity-menu auto-open lease closed; no Android/publisher agent changes.
