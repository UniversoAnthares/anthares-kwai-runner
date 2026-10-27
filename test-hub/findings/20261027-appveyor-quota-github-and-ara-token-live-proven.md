# AppVeyor v1 credential and Anthares Remote fallback: confirmed live
STATUS: PROVEN
AREA: GitHub Actions / AppVeyor API / Anthares Remote / RSA sealed handoff
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40550379297
JOB: 122352172133
COMMIT: 4ea23d5e5e351baadae4bab2d7ca169b4bb7de92
SUPERSEDES: test-hub/findings/20261027-ara-quota-standby-rsa-production-auth-live-partial.md

## Confirmed
1. GH run #40549166660 used the owner-provisioned GitHub Actions secret APPVEYOR_API_TOKEN; authenticated GET on the exact UniversoAnthares/anthares-kwai-runner AppVeyor project returned `APPVEYOR_AUTH_PROBE=VERIFIED_SCOPE_ACCOUNT_V1`; no secret printed.
2. Vercel production deployed RSA public JWK endpoint and authenticated GH OIDC staging route `/api/credential-bridge`; DB additive migration `db/migrations/20261027_ci_quota_sealed_remote_credential.sql` created restricted `public.anthares_ci_quota_sealed_credentials`, granting only `anthares_ci_quota_limited`.
3. GH run #40550379297 returned `APPVEYOR_AUTH_PROBE=VERIFIED_SCOPE_ACCOUNT_V1` and `ARA_TOKEN_TRANSFER=SEALED_READY`. Node RSA-3072 OAEP encrypted inside GH runner; only ciphertext entered Vercel and Neon. Private key remained SYSTEM DPAPI on Windows.
4. Anthares Remote SYSTEM successfully consumed the one-time sealed envelope, decrypted privately, made a SECOND exact project read-only AppVeyor API request, then wrote an isolated DPAPI-protected secret `D:\AntharesWork\AntharesRemote\secrets\ci-quota-appveyor-token.dpapi`. Output: `credential_import=IMPORT_VERIFIED_AND_DPAPI_PROTECTED`, `controller=READY_RSA_NEON`, `appveyor=READY_EVENTS_0`, `bitrise=NOT_CONFIGURED`.
5. Credential file ACL: only Administradores and SISTEMA with Full permissions. Windows scheduled task `Anthares CI Quota Cancel Standby` remains Ready as SYSTEM, previous task result 0 and next run scheduled. The one-time Neon bridge has 0 pending sealed records after consume.
6. PR #1592 merged and in production, with workflow and local source on main. No real quota incident was created or observed; **canceling a live AppVeyor build remains unproven**. No CI build triggered, no unexpected publisher effects, no paid plan changes.

## Consequences
- AppVeyor provider credentials NOW configured for both GitHub Actions and Anthares Remote; previous `NOT_CONFIGURED` findings are superseded for AppVeyor. Do not ask for another AppVeyor token.
- Bitrise API token remains absent. Existing Bitrise Hobby executor ineligible for dispatch due to previous machine configuration; this work did not change that.
- Existing cancellation logic remains guarded by provider-structured quota evidence, remote status checks and shared cross-host Neon first-winner fencing. `READY_EVENTS_0` proves authenticated monitor readiness, not cancel-on-real-incident.
- One-time sealed credential transport only supports AppVeyor and is limited to push/dispatch from exact GH quota workflow, RSA signature from Windows device; use the same documented scheme only with explicit independent provider integration and tests.
