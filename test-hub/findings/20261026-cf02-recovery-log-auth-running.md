# CF02 historical production receipt: provider job-log 401 redirect auth fix
STATUS: RUNNING
AREA: github,cloudflare
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40328831002
JOB: 121592588251
COMMIT: f5cf30ee7ce9d90f1ca4af49b16bf4037cdcfc85
SUPERSEDES: test-hub/findings/20261026-cf02-prod-receipt-recovery-running.md
LEASE_AREA: cf02-production-receipt-recovery-no-deploy
LEASE_OWNER: ChatGPT-CF02
LEASE_BASE: fix/cf02-recovery-log-auth-20261026@f5cf30ee7ce9d90f1ca4af49b16bf4037cdcfc85
LEASE_SCOPE: ONLY branch fix/cf02-recovery-log-auth-20261026, targeted Python request redirection fix and unit tests; no touch original deploy job, queues, Cloudflare secrets or production receipt until new verified recovery run.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
Original release flow successfully deployed production Cloudflare, cleaned old Kwai protected queue safely, and health passed on GitHub run 40283336472; receipt PUT 409 failed. CAS source fix #1346 merged. Dedicated recovery workflow #1448 merged f5cf30ee7ce9d90f1ca4af49b16bf4037cdcfc85, branch QA run 40328373173 and PR QA 40328507686 passed; prod recovery job #121592588251 FAILED HTTP401 during evidence API request, with no receipt write. Main receipt remains prior blob 47faf493a965be52cf57ea8780cc61f68510567f. Preflight CF02-RECEIPT-VALIDATION-20261026 exited 0. Local GitLab peer read before write required.

## FAILED_AVOIDED
Do not rerun the unchanged failing evidence-fetch source, do not redeploy Cloudflare or invoke cleanup-legacy-kwai. Never forward short-lived GH_TOKEN on GitHub logs 302 redirect to another hostname. Do not read or output tokens. Identify whether HTTP401 occurs at GitHub metadata vs cross-host log signed URL, and retry only after correcting this cause.

## SUCCESS_SIGNAL
QA tests and GH Actions live run validate cross-host Authorization stripping; main recovery receives verified logs, checks same pinned original production evidence, saves a provenance-labeled receipt with CAS, and independent GET returns it.

## FAILURE_SIGNAL
If GitHub Actions GH_TOKEN lacks source-run access or signed log endpoint remains 401, classify PARTIAL and preserve original receipt. No alternate credential bypass of an explicit authorization denial.

## TEST_VALIDITY
Technical HTTP401 diagnosed by instrumenting stages and protecting cross-host redirects; no changes to social publishers, secrets or Cloudflare Worker in recovery process. Historical attestation, not a new production deploy.
