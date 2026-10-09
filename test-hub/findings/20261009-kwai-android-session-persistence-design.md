# Kwai Android session persistence — design and security gate
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-09
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Baseline
The hosted Android workflow installs Kwai and Anthares Agent and can dispatch a synthetic MP4. User reports the share test passed. Existing AVD is restored from an unauthenticated snapshot, launched with -no-snapshot-save and destroyed with the hosted runner.

## Proposed implementation
1. Use a dedicated, access-controlled remote Android instance or a complete encrypted AVD state (userdata, snapshots, emulator config and matching device/Keystore state). An ephemeral GitHub Actions runner alone cannot maintain a running device.
2. On first boot, authenticate through the official Kwai UI with user participation; independently verify the account handle before any publication.
3. Quiesce the emulator and create a consistent full-state checkpoint. Encrypt client-side before upload to a PRIVATE storage location; do not publish to artifacts, cache, releases, issues or logs in the public repository.
4. On a new runner, restore only an integrity-verified checkpoint into the matching Android image/AVD and validate login and exact account identity. If identity fails, stop and require legitimate reauthentication.
5. Rotate checkpoints with single-writer lease, fencing generation, checksum, retention and rollback protection. Never export cookies/tokens independently or claim Android Keystore portability.
6. Keep video publication disabled until a fresh-run authenticated restore is demonstrated twice and a real post is independently confirmed.

## Acceptance
SUCCESS_SIGNAL: authenticated identity @universo.anthares confirmed in two independent Android lifecycles after checkpoint restore, with no secrets in public logs.
FAILURE_SIGNAL: lost login, wrong identity, Keystore errors, unavailable private encrypted storage, or Android device mismatch.
TEST_VALIDITY: distinguish snapshot load and account UI validation; an APK install or ACTION_SEND alone is insufficient.
FAILED_AVOIDED: repeated UA/CDP mobile-web emulation and unauthenticated ephemeral emulator restarts.
## Current blocker
No confirmed persistent private storage + encryption key management + authenticated Android baseline. Do not checkpoint unauthenticated state and label it persistence.
