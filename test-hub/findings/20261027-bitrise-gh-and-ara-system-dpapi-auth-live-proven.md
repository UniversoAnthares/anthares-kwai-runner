# Bitrise credential active in GitHub and Anthares Remote SYSTEM, verified live
STATUS: PROVEN
AREA: CI quota / Bitrise / Anthares Remote / RSA bridge
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40560325026
JOB: 122387276378
COMMIT: 8a3893d636786eaa37847509e7113dd87c97d54d
SUPERSEDES: test-hub/findings/20261027-bitrise-gh-oidc-rsa-transfer-live-proven-local-import-pending.md

## Result confirmed independently across hosts
- GitHub Actions run 40560325026 returned BITRISE_AUTH_PROBE=VERIFIED_PROJECT_AND_REPO, ARA_BITRISE_TOKEN_TRANSFER=SEALED_READY, QUOTA_EVENTS=NO_STRUCTURED_EVENTS; AppVeyor scope-v1 also verified.
- After user encountered a .NET File.Replace(path,tmp,null) exception, ARA agent completed atomic replacement using a valid non-null temporary backup; parser 0 issues and preserved previous source until validation.
- The first Bitrise import consumed an encrypted envelope but failed as IMPORT_FAILED_AFTER_CONSUME. Production root cause found with local read-only PowerShell parse proof: `@('https://github.com/'+$Repo,...)` unexpectedly produced ONE concatenated string instead of three distinct repository URL entries. This made -notcontains reject a valid Bitrise repo. Fixed in both ImportSealedBitrise and the periodic Bitrise watcher by parenthesizing three array elements; local test yielded COUNT=3 MATCH=True. PR #1616 merged.
- Source installed atomically on Windows from merge 8a3893d636786eaa37847509e7113dd87c97d54d. Actual Windows Task Scheduler job `Anthares CI Quota Cancel Standby` executed as SISTEMA at 2026-10-27T14:29:29-04:00, returned LastTaskResult=0.
- Actual remote status now reads `auth=READY_DPAPI_SYSTEM`, `controller=READY_RSA_NEON`, `bitrise_credential_import=IMPORT_VERIFIED_AND_DPAPI_PROTECTED`, `bitrise=READY_EVENTS_0`, `appveyor=READY_EVENTS_0`, `remote_cancellations_confirmed=0`.
- Windows DPAPI file `D:\AntharesWork\AntharesRemote\secrets\ci-quota-bitrise-token.dpapi` exists with ACL restricted to NT AUTHORITY\SYSTEM and BUILTIN\Administrators, no other entries. Neon sealed_bitrise table contains zero rows (consumed exactly once) and Neon quota_attempts count for Bitrise is zero (no synthetic failures or cancellation). Scheduler principal SYSTEM, LastTaskResult=0, next run scheduled; no leftover .new script.
- Bitrise provider API token no longer needs user intervention. Both GH watcher and ARA standby can use it; ledger fencing prevents duplicate cancels for a real structured quota incident.

## Remaining distinction
- PROVEN: authenticated Bitrise API GET, project and repo ownership, secure token import to SYSTEM DPAPI, ready scan.
- NOT PROVEN: Bitrise cancellation for a real quota-blocked build. Do not simulate a quota failure or claim universal provider cancellation.
- Separate Bitrise Hobby runner is still ineligible as job EXECUTOR due to prior `invalid default machine elite`; availability as cancel controller does NOT prove runner usability. No paid plan change.
- This finding supersedes earlier reports of Bitrise NOT_CONFIGURED; maintain safe fail-closed handling for missing structured quota evidence.
