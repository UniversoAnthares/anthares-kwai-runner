# PR #1557 — AppVeyor/Bitrise quota cancel watcher deployed, credentials pending
STATUS: PARTIAL
AREA: github-ci/quota-provider-cancel
DATE: 2026-10-27
RUN: https://vercel.com/lucasyahn-6808/anthares-ci-quota-controller
JOB: none
COMMIT: f9eac8cd6d46a7c9e9315d7c5be17bf836616efa
SUPERSEDES: test-hub/findings/lease-20261027-multiprovider-real-cancel-chatgpt.md

## Real implementation
- PR #1557 merged into main; publishes tools/ci_quota_external_watcher.py and workflow ci-quota-external-cancel.yml.
- Scheduled GitHub hosted watchdog every 15 minutes, plus manual workflow_dispatch; GitHub OIDC restricted to exact workflow/ref/repo.
- Reads authorized AppVeyor and Bitrise builds, accepts only exact machine-readable quota code verified on the same build, main branch, full SHA and matching UniversoAnthares/anthares-kwai-runner repository.
- Atomic one-winner claim in public.anthares_ci_quota_attempts (Neon production) precedes provider-specific cancellation. AppVeyor uses DELETE /api/builds/{account}/{project}/{version}, Bitrise POST /apps/{app}/builds/{slug}/abort. Readback reports terminal or CANCEL_UNCONFIRMED and never resubmits unknown jobs.
- Vercel production deployment dpl_Cf8H3Z6AbfsHuXGcC9pZVZBpMS2N READY; HTTP GET /api/health=200, ledger=READY, mode=ENABLED and GET /api/provider-cancel=405. New endpoint persists claim/report only, never receives AppVeyor/Bitrise API tokens.
- Provider tokens must reside in GitHub Actions repository secrets APPVEYOR_API_TOKEN and BITRISE_API_TOKEN. Exact project identity is provided with vars APPVEYOR_ACCOUNT, APPVEYOR_PROJECT and BITRISE_APP_SLUG.

## Operational boundary, no invented proof
- No actual AppVeyor or Bitrise quota incident was observed/processed after this deployment.
- No confirmation that above tokens/vars are provisioned in GitHub Actions. The available Anthares Remote Windows environment had no provider-prefixed vars, gh CLI is not logged in, bws CLI is not installed. No provider token was copied or printed.
- This does not prove universal cancellation. GitHub Actions quota emitter tools/ci_quota_signal_github.py remains opt-in and is not attached to a producer of a verified structured quota signal.
- If no machine-readable quota code exists for an external provider, fail-closed means no cancellation and no fallback.
- GitLab CI production handoff remains separately PROVEN using pipeline 2994547840 -> GitHub run 40510154187.

## Next gates
- Provision provider API credentials and immutable project vars by authorized secret manager path, never by plaintext commit.
- Confirm true quota incident with remote cancellation terminal receipt (or provider already terminal) and compare ledger to remote.
- Implement provider-specific safe successor only when side effects are reconciled NOT_APPLIED and the successor quota scope is independently verified.
