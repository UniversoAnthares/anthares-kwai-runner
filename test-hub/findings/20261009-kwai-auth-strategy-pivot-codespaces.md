# Switch Kwai authentication strategy to private Codespaces Chrome
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37938604983
JOB: 113846903755
COMMIT: 17be4e57267ec428942ffecd0760d5f8beff910d
SUPERSEDES: 20261009-kwai-auth-first-timeout-root-cause.md

DECISION: Adopt the already-proven private GitHub Codespaces Chrome desktop as the primary interactive authentication route. Android interactive onboarding is not the primary login path after three repeated failures at runs 37947415466, 37947449351, and 37947977836 (KWAI_EMAIL_LOGIN_NOT_VISIBLE and step timeout).
BASELINE_PROVEN: Codespaces desktop smoke 37938604983; guard rejects unauthenticated identity, private ports supported. Chrome Google/phone login UI 37936848163.
FAILED_AVOIDED: Android right-heart onboarding and generic KWAI_OWNER_INTERACTION_READY after unusable UI.
SUCCESS_SIGNAL: real private Codespace Chrome authenticates expected account, identity guard confirms handle, persistent private profile survives restart.
FAILURE_SIGNAL: cannot open private Codespace, login blocked, wrong account, or guard rejects identity.
TEST_VALIDITY: Chrome synthetic smoke is not a real account login. Browser session is not automatically equivalent to Android app session. Publication remains gated.
ACTION: use existing .devcontainer and private 6080/8765 ports; independent Codespaces identity agent continues. No Android runner modification in this architecture handoff.