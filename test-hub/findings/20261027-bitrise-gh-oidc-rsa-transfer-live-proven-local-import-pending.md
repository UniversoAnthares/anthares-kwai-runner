# Bitrise API owned + RSA sealed handoff live; Anthares Remote local upgrade pending
STATUS: PARTIAL
AREA: CI quota / Bitrise / GitHub Actions / RSA bridge / Anthares Remote
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40557059957
JOB: 122375823152
COMMIT: 3fb6da86bb8eec41e1fa946a1e11d6dcfb6456c0
SUPERSEDES: test-hub/findings/20261027-bitrise-rsa-quota-credential-transfer-remote-update-blocked.md

## Live proof
- Real GitHub Actions run 40553500657 on merge #1598, job 122363251837, output `BITRISE_AUTH_PROBE=VERIFIED_PROJECT_AND_REPO`, proving saved GitHub Secrets Bitrise API token is valid for Bitrise app `ef06f940-ffc7-4e37-b935-93ad06d8faeb` and the expected repository. Never printed token.
- Initial merge #1600 run 40554184120 (job 122365683032) failed with `BITRISE_TOKEN_TRANSFER=STAGE_RESPONSE_400` at 17:49:34.805Z UTC. The matching production Vercel deployment `dpl_DwZ1X8MLS9ZAhUDnyJezg4dEmEmu` was created at 17:49:47.882Z UTC, 13s after the request; it subsequently became READY. The request reached a prior API revision, NOT a Bitrise authentication failure.
- PR #1604 merged, removing an exact duplicate Bitrise validation step and preserving the remaining read-only ownership check BEFORE encrypted transfer, plus sanitized controller error classes.
- Live subsequent GitHub Actions run 40557059957 job 122375823152 succeeded. Decisive log lines:
  - `APPVEYOR_AUTH_PROBE=VERIFIED_SCOPE_ACCOUNT_V1` at 18:08:00Z;
  - `BITRISE_AUTH_PROBE=VERIFIED_PROJECT_AND_REPO` at 18:08:02Z;
  - `ARA_BITRISE_TOKEN_TRANSFER=SEALED_READY` at 18:08:03Z;
  - `QUOTA_EVENTS=NO_STRUCTURED_EVENTS`.
- Neon production `public.anthares_ci_quota_sealed_bitrise` contains one ciphertext-only row: source_run=40557059957, length=512, expires_at=2026-10-27T19:38:02.992Z. No plaintext was written to Neon, Vercel, or Git. This pending envelope is not yet consumed.
- Read-only Anthares Remote check: device DESKTOP-FTDK0HP connected; current local script `D:\AntharesWork\AntharesRemote\source\ci-quota-cancel-standby.ps1` DOES NOT contain `function ImportSealedBitrise`; local SYSTEM DPAPI file `ci-quota-bitrise-token.dpapi` ABSENT. Existing scheduled task LastTaskResult=0. Earlier attempt to upgrade this local script was explicitly rejected by tool security controls; do not reroute remote write to evade it.

## Meaning and next gate
- PROVEN: Bitrise GH token authenticated for own app, encrypted transfer successfully staged to intended remote recipient, existing AppVeyor path unchanged.
- NOT PROVEN: Anthares Remote Bitrise DPAPI import, remote Bitrise watcher readiness, real Bitrise quota cancellation, or eligible Bitrise CI executor on Hobby (prior machine-type problem remains).
- Require authorized manual local script update to versioned GitHub main source, syntax-check and then run SYSTEM scheduled task to consume envelope. If after 2026-10-27T19:38:02Z, re-stage only through authorized GitHub Actions workflow_dispatch when actual controller READY; no ad-hoc token/plaintext transfer or unsafe provider action.
- Preserve the previous script until parsed replacement is verified; do not disclose credentials.
