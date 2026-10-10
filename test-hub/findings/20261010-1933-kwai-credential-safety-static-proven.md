# Kwai credential containment and fail-closed publication safety
STATUS: PROVEN_STATIC
AREA: kwai-publish
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38080087898
SUPERSEDES: test-hub/findings/20261010-1930-lease-kwai-reconcile-real-remote-id.md

## Verified
- Public publisher artifact purge succeeded, 18 artifacts removed: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38079625643.
- Public publisher workflow no longer schedules automatic login or uploads login screenshots; its publish job requires `vars.KWAI_CREDENTIALS_ROTATED == 'true'`.
- `kwai_headless_login.sh` and `kwai_remote_android_login.sh` no longer save login screenshots; remote script no longer copies raw login XML into artifact files.
- Both `tools/kwai_credential_login.py` (canonical) and `kwai_android_autologin.py` require a positively identified password EditText; ambiguous generic field fallback removed.
- `kwai_queue_state.sh reconcile` rejects absent/fabricated remote post identity; it never creates `remote_id` from queue job ID.
- Dedicated no-credential CI static gate passed: run 38080087898. Earlier runs 38080081316 and 38080013674 also passed.

## Still blocked
- Previously exposed Kwai password MUST be rotated in Kwai and GitHub secret KWAI_PASSWORD updated; never assert old password is safe because artifacts were deleted.
- User or authorized identity owner must complete any external OTP/CAPTCHA; cannot claim READY until independent profile UI confirms expected account.
- No verified real Kwai post ID, no real publication, no session persisted across two remote lifecycles. Queue remains fail-closed.
