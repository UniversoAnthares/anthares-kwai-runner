# Browser-only interactive Chrome access in private GitHub Codespaces
STATUS: RUNNING
AREA: kwai-codespaces-browser
DATE: 2026-10-09
OWNER: chatgpt-codespaces-browser
RESOURCES: .devcontainer/kwai-*, .devcontainer/devcontainer.json, tests/test_kwai_codespaces_browser.py, .github/workflows/kwai-codespaces-browser-qa.yml, docs/kwai-codespaces-browser.md
LEASE_UNTIL: 1791554428
BASELINE_PROVEN: 37936848163 browser-only Chrome probe success; phone/Google login UI reachable; session key present but authenticated=false. 37935784822 cross-run synthetic crypto proof; 37936417696 8/8 cache-security tests.
FAILED_AVOIDED: GitHub Actions Chrome is headless/non-interactive; do not expose noVNC via public tunnel or publish credentials; do not reuse Android virtual or local PC as executor; do not assume login from absent button.
SUCCESS_SIGNAL: isolated Codespaces cloud desktop config provides browser-only Chrome via GitHub-authenticated private port, localhost-only VNC/CDP, and fail-closed identity inspector; hosted CI validates config/security and script syntax; real identity only after actual user login.
FAILURE_SIGNAL: public port, browser credentials leaked, plaintext session uploaded, identity asserted without ownership controls, or CI failure.
TEST_VALIDITY: static and hosted smoke QA do not count as real Codespaces instance or successful account login; actual Codespace requires account-owner creation.
CONCURRENCY: distinct from ongoing kwai-login/Android agent leases; no edits to their files, browser probe, crypto harness, or publisher.
