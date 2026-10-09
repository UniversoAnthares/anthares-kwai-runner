# Lease — WordPress extreme plugin QA
STATUS: RUNNING
AREA: wordpress-qa
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
TYPE: LEASE
OWNER: chatgpt
RESOURCES: UniversoAnthares/anthares-wordpress (all plugin code, QA/CI only; no production publication)
LEASE_UNTIL: 1791515220

BASELINE_PROVEN: GitLab main pipeline 2927978106 succeeded on GitLab main 7ec8ae501044a6587f8b2a9e8fea4d4cda161169; GitHub main currently bbe1eed2ea1f19bb32954420317ef602d66480ff. Existing GitLab QA lints all PHP files and checks a narrow Pix Sales regression set.
FAILED_AVOIDED: GitHub Actions runs 37858681000 and 37835315016 ended before runner steps (runner_id=0, steps=[]), so this audit will use GitLab CI as the executable QA path and will treat GitHub Actions as unavailable evidence rather than retrying the same failed harness.
SUCCESS_SIGNAL: complete repository-wide PHP lint plus repository inventory, JS syntax check where applicable, duplicate global function/class scan, include/require target validation, WordPress AJAX/REST security heuristic report, dangerous API/secret-pattern scan, and plugin entrypoint/header inventory execute over every Anthares plugin tree with decisive artifacts/log lines and zero unexplained fatal findings.
FAILURE_SIGNAL: any syntax error, missing required local include, duplicate unconditional global symbol with collision risk, exposed secret material, or high-confidence unauthenticated state-changing endpoint without nonce/capability guard.
TEST_VALIDITY: the QA job must enumerate every top-level Anthares plugin directory/file present in the tested tree and print counts for scanned PHP/JS files; missing checkout, unavailable scanner runtime, or incomplete inventory invalidates the run rather than proving code failure.

Purpose: perform an extreme read-only/code-QA review of all plugin code, fix only evidence-backed defects under read-before-write/peer-provider gates, rerun QA, and append closure evidence.