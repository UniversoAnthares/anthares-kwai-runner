# CF02 QA: GitHub provider CAS real sem Cloudflare deploy
STATUS: RUNNING
AREA: github, cloudflare
DATE: 2026-10-26
RUN: pending
JOB: CF02-REAL-CAS-QA-20261026
COMMIT: 00634f88955321cc94a3c480477a1001ff0b535d
SUPERSEDES: none
LEASE_AREA: cf02-github-cas-provider-qa-isolated-20261026
LEASE_OWNER: ChatGPT-CF02-CAS
LEASE_BASE: anthares-kwai-runner/main@00634f88955321cc94a3c480477a1001ff0b535d
LEASE_SCOPE: ONLY branch evidence/cf02-real-provider-cas-qa-20261026; add Test Hub findings and isolated QA workflow; do not edit main, production receipt .github/cloudflare-cortes-status.json, existing publisher workflows, Cloudflare or secrets.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
PR #1346 integrated into main commit 00634f88955321cc94a3c480477a1001ff0b535d with [skip ci] to avoid an automatic production deploy. Prior CI regression test #40157117628 succeeded, using mocked HTTP409. Workflow source has 3-attempt CAS retry, hosted test code in tests/test_cloudflare_receipt_cas.py. Last real production receipt .github/cloudflare-cortes-status.json is dated 2026-10-19 and must remain unchanged until an authorized deploy. CF02 staging rollback proven independently by PR #1402. Governance main manifest 2e28d54043d6bad1 and Windows local f6fc9ca59a96e451 remain divergent; preflight run CF02-RELEASE-20261026 exit0.

## FAILED_AVOIDED
Do NOT dispatch or rerun .github/workflows/cloudflare-central-deploy.yml, invoke queue maintenance endpoint, create social content, change the production receipt, copy tokens, alter main, or bypass security denial. Avoid any workflow with secret injection beyond ephemeral GITHUB_TOKEN scoped to isolated QA branch. No production deploy in this test.

## SUCCESS_SIGNAL
A scoped GitHub Actions workflow on the QA branch extracts the ORIGINAL integrated receipt Python code; substitutes ONLY receipt filename and branch into an isolated QA namespace; obtains real GitHub content SHA, forces one REAL HTTP409 with a synthetic competing write using the same GitHub API, observes receipt retry refreshes SHA and writes successful QA JSON. Readback evidence records `provider_http409=true`, `retry_saved=true`, `qa_branch_only=true`, no production changes.

## FAILURE_SIGNAL
If permissions, jobs or API prevent real test, classify NOT_TESTED/PARTIAL with evidence; do not send retries to production and do not claim success from mock only.

## TEST_VALIDITY
Real GitHub REST API and actual workflow receipt source under branch-scoped QA; no Cloudflare deploy, no real publisher health/maintenance, no production receipt, no proof of full production E2E.
