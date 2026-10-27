# Bitrise credential rollover — integration installed, authenticated run not yet verified
STATUS: PARTIAL
AREA: CI quota / Bitrise / Anthares Remote
DATE: 2026-10-27
RUN: none confirmed
JOB: none confirmed
COMMIT: 3498ff9b8e63d6637d77182d5e79d08751889827
SUPERSEDES: test-hub/findings/lease-20261027-bitrise-rsa-credential-transfer.md

## Real changes
- User confirmed that BITRISE_API_TOKEN was saved in GitHub Actions repository Secrets. Secret VALUE and validity were not exposed to assistants.
- PR #1598 merged, adding fail-closed Bitrise API GET authorization and ownership verification in the deployed GitHub Actions quota workflow. It must verify slug ef06f940-ffc7-4e37-b935-93ad06d8faeb and exact GitHub repo before any sealed handoff step.
- PR #1600 merged, adding RSA-OAEP sealed Bitrise credential handoff from GitHub Actions via OIDC to Vercel and recipient-only decryption on Windows SYSTEM. Uses existing RSA public JWK and DPAPI private key. Provider-specific row resides in new independent restricted Neon table public.anthares_ci_quota_sealed_bitrise (no AppVeyor table schema modifications).
- Vercel deployment dpl_DwZ1X8MLS9ZAhUDnyJezg4dEmEmu READY. Neon bitrise sealed table creation confirmed, count=0 when checked.
- PowerShell source on repo main includes ImportSealedBitrise and was parsed on Windows from branch with 0 syntax errors prior to merge.
- The attempt to replace Windows local scheduled watcher script was blocked by tool security restriction. Do not infer Windows deployment; do not use other remote-control channels to circumvent explicit rejection.
- Fetching GitHub workflow run list through remote_exec was separately blocked. No Bitrise credential probe result or sealed transfer receipt independently confirmed in this round.
- Bitrise Hobby runner remains INELIGIBLE to run jobs until separate invalid-default-machine-elite issue fixed; token auth does NOT imply successful runner.
- AppVeyor remains PROVEN configured in both GH and Anthares Remote (independent previous finding); no changes in this PR touched its workflow ownership or local credential.

## Final gates
1. Read native GitHub Actions run summary of .github/workflows/ci-quota-external-cancel.yml after PR #1600 merge: require BITRISE_AUTH_PROBE=VERIFIED_PROJECT_AND_REPO and ARA_BITRISE_TOKEN_TRANSFER=SEALED_READY; a green infrastructure deploy alone does not satisfy this.
2. Once the Windows remote script change is permitted, update deployed SYSTEM script from main, check parse 0, execute once and require bitrise_credential_import=IMPORT_VERIFIED_AND_DPAPI_PROTECTED AND bitrise=READY_EVENTS_0; preserve current DPAPI AppVeyor secret and task trigger.
3. Only a real Bitrise structured-quota incident, a confirmed provider terminal readback, and matching shared Neon attempt prove Bitrise cancel-first operational. Do not fabricate quota events or claim universal completion.
