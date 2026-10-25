# R07.6 item 13 — verificador read-only no executor GitHub Linux
STATUS: RUNNING
AREA: architecture / tiktok / ISO-07
DATE: 2026-10-25
OWNER: chatgpt-iso07
JOB: ISO07-20261025-RETAKE
BRANCH: chatgpt/r07-iso07-readiness-qa-20261025
SUPERSEDES: none

## BASELINE_PROVEN
Test Hub finding 20261025-iso07-readiness-windows-proven.md: 10/10 unittest passed on real Windows, inspector returns BLOCKED with 22 gates against GitHub workflows/Neon read-only snapshot; no publication. PR draft #1396 with no deployment. Fresh governance preflight f6fc9ca59a96e451 PASS; previous Neon / GitHub Environment mutations denied; production remains untouched.

## FAILED_AVOIDED
Do not rerun destructive/provisioning attempts that were rejected; do not write to production Neon; do not publish social media; do not use credentials, OIDC, personal browser, Windows processes or GitHub admin permissions. No changes to other agents' branches, workflows or Test Hub historical findings.

## SUCCESS_SIGNAL
A GitHub-hosted Linux runner on the isolated PR branch runs the 10 tests against the same read-only code and diagnoses the current repository workflows as BLOCKED, authorized_to_publish false and live_publication_invoked false. Record run URL, commit and decisive logs. No secret accesses or publisher calls.

## FAILURE_SIGNAL
Any test fails, no decisive test output, workflow not scheduled, evidence unexpectedly says production allowed, script invokes real publisher or runs with elevated permissions.

## TEST_VALIDITY
Only QA harness independent of Windows/Neon, not production IAM or external canary. GitHub Actions usage is existing CI quota; no new paid services. No production deploy or secrets. Completion requires evidence from actual hosted job, not commit status alone.

## LEASE
Only newly created .github/workflows/cortes-iso07-readonly-qa.yml and this finding, inside our existing exclusive PR branch. Do not edit other agent files; safely rollback by closing draft PR.
