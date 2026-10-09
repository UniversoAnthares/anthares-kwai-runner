# Independent cloud Chrome Kwai web reachability validation
STATUS: RUNNING
AREA: kwai-codespaces-browser-webreach
DATE: 2026-10-09
OWNER: chatgpt-browser-only
LEASE_UNTIL: 1791554601
RESOURCES: .github/workflows/kwai-codespaces-browser-smoke.yml, .kwai-codespaces-smoke-trigger
BASELINE_PROVEN: 37938604983 Chrome/noVNC/private inspector passed, no authenticated identity. 37938795559 security QA passed.
FAILED_AVOIDED: no assumption that a responding CDP endpoint means kwai.com loaded. No Android, no local PC, no credentials, no public VNC. Do not modify active kwai-login agent or publisher.
SUCCESS_SIGNAL: independent hosted cloud Chromium CDP navigates to https://www.kwai.com/ and reports final origin, title, HTTP status and presence of login controls without disclosing cookies, tokens, or query parameters.
FAILURE_SIGNAL: timeout, network or TLS failure, wrong origin, HTTP blocking or browser crash recorded separately from harness failure.
TEST_VALIDITY: probe must run within existing GitHub-hosted Debian Chrome container and complete within bounded timeout; no real Codespace or login claim.
