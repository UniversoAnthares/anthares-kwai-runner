# Lease: Kwai authentication and private persistence proof
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-10
OWNER: chatgpt-kwai-persistence-proof
LEASE_UNTIL: 2026-10-10T03:31:00Z
HEAD_BASELINE: 68d788606d5e050544669332c6eb2786db6bc826
RESOURCES: .github/workflows/kwai-interactive-remote-login.yml; kwai_session_state.sh; private checkpoint storage provisioning
BASELINE_PROVEN: hosted Android boots; official Kwai APK is installed; secret-backed login flow and encrypted local session save/restore code exist; current run 38018952625 is authenticating and no real publication is part of this proof.
FAILED_AVOIDED: no desktop-browser substitute; no public artifact/cache as final authenticated storage; no logout/session deletion; no real publication; no PC runtime; wait for current same-chain run before mutating login workflow.
SUCCESS_SIGNAL: authenticated official Android UI identity is independently verified; encrypted checkpoint is stored in access-controlled private zero-cost storage; two fresh independent hosted Android runs restore it and verify the expected account without new login.
FAILURE_SIGNAL: authentication requires unavailable interactive MFA/captcha; private zero-cost storage cannot be provisioned; encrypted state cannot be restored; restored identity differs from expected account.
TEST_VALIDITY: each persistence proof must start a fresh GitHub-hosted Android lifecycle and verify identity from the official com.kwai.video UI after restoration, not from synthetic files or cache presence alone.
