# Kwai Android native login: bounded diagnostic instrumented, real run pending
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-10
OWNER: chatgpt-qa-handoff-1859Z
SUPERSEDES: 20261010-1859-lease-kwai-login-xml-selector-repair.md

## Evidence
- Real Android run 38078174966: app launched at 19:04:01Z, then native login chooser not reached in 110s; failed exit 34 at 19:05:53Z. No login or publication. Previous UI state was not logged, so exact blocking screen cannot be inferred.
- Added privacy-safe UI classifier tools/kwai_ui_safe_diagnose.py (commit ed2d679) and 10 synthetic tests tests/test_kwai_ui_safe_diagnose.py (commit d5888f0).
- Replaced blind loop in kwai_native_email_smoke.sh (commit 11104c0) with bounded state machine: only taps onboarding on positively identified interest screen, profile on positively identified tab; records boolean UI signatures, counts valid/invalid dumps and safe blockers; stops after 95s or 12 onboarding taps.
- Existing selector quickcheck 38078710516 passed at SHA 11104c0 (shell syntax and 15 selector tests). The new 10 classifier tests have not yet run in GitHub Actions. No second Android run was dispatched.
- Attempt to extend quickcheck workflow was blocked by tool security settings. Do not rerun old failed run (same old SHA), or claim new code validated end-to-end.

## Next action
After authorized workflow edit/dispatch access is restored, include tests/test_kwai_ui_safe_diagnose.py in the fast quickcheck, run a single new 5-minute Android diagnosis on updated SHA and inspect allowlisted UI_STATE / BLOCKER lines. Repair the actual observed blocker; do not repeat blind onboarding or 40-way QA. Keep Cloudflare v16 and identity verification as separate gates.
