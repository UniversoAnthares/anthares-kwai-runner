# First real publisher run after private vault integration
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38083505397
JOB: 114305117466
SUPERSEDES: test-hub/findings/20261010-2028-kwai-private-kv-oidc-two-independent-runs-proven.md

## Evidence
- Real publisher GitHub workflow parsed successfully: login_recovery_syntax SUCCESS, control_preflight SUCCESS, publish job reached remote Android.
- OIDC authenticated private Cloudflare KV restore: KWAI_PRIVATE_VAULT_STAGE=control_health, github_oidc, vault_request; KWAI_PRIVATE_VAULT_SESSION_ABSENT=1; KWAI_PRIVATE_VAULT_EMPTY_BOOTSTRAP=1.
- Android emulator launched Kwai, but authenticated account identity NOT proven. KWAI_AUTH_STATE=AUTHENTICATED_OPERATIONAL then KWAI_AUTH_STATE=UNKNOWN_CREATE_SURFACE_NOT_IDENTITY_PROOF.
- Native credential login returned KWAI_AUTO_LOGIN_FALLBACK_REQUIRED_RC=3. Canonical publisher exited 64 before queue claim or publish.
- Private vault upload correctly skipped: KWAI_PRIVATE_VAULT_SAVE_SKIPPED_NO_SESSION=1.
- No credential or session blob stored in public GitHub cache or artifacts.
- Dedicated nonsecret Cloudflare KV canary succeeded across independent runs 38083658324 and 38083802289; this does not substitute for account identity proof.

## Next causal step
- Resolve native login surface / account identity via legitimate user-authorized app UI or a previously authenticated remote browser session.
- Do not re-run the same Android login blindly: no observed account EditText and no confirmed authenticated profile.
- Only after account proof, save encrypted app state to private KV, restore on two fresh runners, then post one video and verify independent public URL and post ID.
