# Canonical Kwai publisher v16 preflight proven; native login is the blocker
STATUS: FAILED
AREA: kwai-publish
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38078684904
JOB: 114290934518
COMMIT: 1b7ed110d8328696ae8f9baaff610715122ed414
SUPERSEDES: test-hub/findings/20261010-1913-cloudflare-v16-deployed-publisher-running.md

## Evidence
- control_preflight SUCCESS against live Cloudflare queue-fencing-v16; secrets presence, vault checksum, KVM and Android APK installation SUCCESS.
- Cache restore: `Cache not found for input keys: kwai-session-Linux-...`; `KWAI_SESSION_CACHE_MISS`.
- Android app interactive; autofill returned `KWAI_AUTO_LOGIN_FALLBACK_REQUIRED_RC=3` after landing on native chooser `Continue with Google | or use Facebook | Phone | Email` (no real EditText).
- Probe emitted `KWAI_AUTH_STATE=UNKNOWN_CREATE_SURFACE_NOT_IDENTITY_PROOF`; publisher failed closed at exit 64. No queue claim, no post, no authenticated session evidence.
- The message `KWAI_AUTH_STATE=AUTHENTICATED_OPERATIONAL` is an exploratory create-surface signal and MUST NOT be treated as identity proof.

## Causal follow-up
- `tools/kwai_android_login_entry.py` selects Email/Phone by exact substring geometry, not center tap; `kwai_android_autologin.py` invokes selector, removes raw UI debug and the old phone probe. Commits fadea565, 63f7c28, e44b82b.
- 8 targeted synthetic tests added in `tests/test_kwai_android_login_entry.py` commit 2db8b9a.
- New bounded Android diagnostic run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38079218107 is in progress at 19:20Z. Existing 40-way QA suite must not be repeated.
- Next canonical publisher run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38079188085 is also in progress; do not dispatch duplicate.

## Gate
Identity must be observed from the actual profile UI, encrypted session must restore in two independent remote lifecycles, and publication must have independent remote evidence. No claim of success until these gates are proven.
