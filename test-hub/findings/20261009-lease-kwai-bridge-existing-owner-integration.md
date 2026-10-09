# Lease: integrate existing-tab identity helper into bridge v2
STATUS: RUNNING
AREA: kwai-codespaces-bridge-owner-integration
DATE: 2026-10-09
OWNER: chatgpt-bridge-owner-integration
LEASE_UNTIL: 2026-10-09T18:30:00Z
HEAD_BASELINE: e279b2be305708c4e6f4f97a4eec78ce60b9f085
RESOURCES: .devcontainer/kwai-command-bridge-v2.py
BASELINE_PROVEN: run 37967009469 SUCCESS for isolated helper; live bridge v2 responds to commands; authentication visible but exact identity unverified.
FAILED_AVOIDED: disposable public profile Edit profile false negative; no login reset, no Chrome restart, no Android.
SUCCESS_SIGNAL: bridge owner_probe invokes existing-tab helper and returns only redacted booleans; CI syntax/tests pass; live owner_probe independently required for identity proof.
FAILURE_SIGNAL: import failure, unsafe session mutation, false positive from public feed link, or live owner check remains false.
TEST_VALIDITY: CI success validates integration code only; live Codespace response is required for identity verification.
PEER: GitLab 87307248 bridge v2 path 404; do not blind mirror.
