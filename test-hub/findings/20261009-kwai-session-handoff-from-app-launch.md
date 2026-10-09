# Kwai authenticated-session handoff after app-launch proof
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37940202375
JOB: 113852336706
COMMIT: 18e9a9e369ceaa9ba84de6b89517e46b6cf904b8
SUPERSEDES: none

## BASELINE_PROVEN
GitHub-hosted cached parallel-v5 Android restored kwai-ready; installed Kwai splits and opened com.kwai.video/com.yxcorp.gifshow.tiny.TinyLaunchActivity. Run 37940202375 job 113852336706: KWAI_APP_FOREGROUND=true, KWAI_APP_READY_TOTAL_SECONDS=75. No authenticated account inferred.

## Independent read-only diagnostics
Existing interactive login runs 37940330000 job 113852768706 and 37940318452 job 113852728836 both concluded failure at 'Interactive owner login or validated restore'. Both logged KWAI_SESSION_CACHE_MISS_BEFORE_LOGIN, KWAI_SESSION_RESTORE_GATE_FALLBACK_INTERACTIVE and KWAI_LOGIN_UI_OPENED, then exit code 2. Therefore login UI discovery is real, but credentials/session acceptance, encrypted persistence, account identity and cross-run restoration remain OPEN.
The Chrome-only path separately proved KWAI_SESSION_KEY present in run 37936848163 but authenticated=false, encrypted_session_found=false and identity_verified=false. Synthetic encrypted-state QA is not proof of real authentication.

## FAILED_AVOIDED
Do not repeat Android boot benchmarks, bare ikwai login-router probes, or blind feed login clicks. Do not mistake an opened login form, cached feed or successful synthetic cryptography for an authenticated identity.

## Next causal handoff to kwai-login owner
1. Investigate exact exit-2 condition AFTER KWAI_LOGIN_UI_OPENED in login-agent runtime, using redacted logs and strict form/account-identity evidence.
2. After successful owner authentication, encrypt session state and verify restore on a separate GitHub-hosted runner; assert expected account identity before publishing.
3. Preserve no-session fail-closed gate; do not expose secrets/cookies in public logs or artifacts.

## Constraints
Read-only inspection of login-agent runs; no login-agent file modifications, no session mutation, no PC. No competing lease acquired in kwai-login area. No new login workflow dispatched because another agent owns that chain.
