# Lease: Kwai Android interactive authentication and private persistence
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-09
OWNER: chatgpt-android-auth-persistence
LEASE_UNTIL: 2026-10-09T19:08:00Z
HEAD_BASELINE: 7a960887fbf16b31185500b6796b438c20f4678e
RESOURCES: .github/workflows/kwai-android-interactive-login.yml; private checkpoint storage provisioning only
BASELINE_PROVEN: official Kwai Android APK installs and launches on hosted cloud Android; run 37972443158 is green but explicitly proves no authentication, and the synthetic encrypted-checkpoint roundtrip is not an authenticated-session proof.
FAILED_AVOIDED: do not reuse desktop Chrome/Codespaces as Android authentication; do not infer login from app launch or ACTION_SEND; do not store Android session material, cookies, tokens, passwords, screenshots, or plaintext checkpoint state in the public repository/artifacts/cache/logs.
SUCCESS_SIGNAL: official Kwai Android UI is exposed through a temporary authenticated remote GUI; user completes legitimate login/MFA if required; exact @universo.anthares identity is verified without emitting sensitive UI/session data; a full encrypted checkpoint is written to access-controlled private storage and restores successfully in two independent Android lifecycles.
FAILURE_SIGNAL: remote GUI is unauthenticated/public, login identity cannot be verified, private storage/key management is unavailable, checkpoint restore loses authentication, or any sensitive state would be exposed publicly.
TEST_VALIDITY: GUI/app must be official Android com.kwai.video on a hosted cloud emulator; browser-only login, synthetic state, or install/launch success is invalid as authentication evidence.
CONCURRENCY: active lease 20261009-lease-kwai-owner-multisignal.md uses AREA kwai-existing-tab-owner-helper and resource .devcontainer/kwai-existing-tab-owner.py; this lease does not mutate that resource or browser-session chain.
