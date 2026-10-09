# Exact owner verification from bounded authenticated menu subtree
STATUS: RUNNING
AREA: kwai-existing-tab-owner-helper
DATE: 2026-10-09
RUN: none
JOB: none
COMMIT: d3c01ce975627608edc5ec4b45db1040c80705a0
SUPERSEDES: 20261009-kwai-owner-react-settings-failed.md
BASELINE_PROVEN: authenticated session is repeatedly proven by visible Log out; exact owner evidence remains absent from public profile, logout ancestry, label-only menu navigation, generic account-row clicks, and hydration state.
FAILED_AVOIDED: scan only the logout ancestry was too narrow. New probe scans React props/fibers on every element inside the bounded authenticated dropdown and, if needed, only non-dangerous geometric targets above Log out.
SUCCESS_SIGNAL: bounded menu subtree contains exact expected handle/profile route tied to its React props, or a safe account-row target navigates to exact /@universo.anthares; live owner_probe returns identity_verified=true.
FAILURE_SIGNAL: both bounded subtree and geometric account-row evidence remain false.
TEST_VALIDITY: QA validates syntax/security only; live Codespaces result is required. No cookies/storage/tokens/raw page text/screenshots exported and no publish action.
