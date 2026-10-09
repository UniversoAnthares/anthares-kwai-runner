# Lease renewal — WordPress extreme plugin QA
STATUS: RUNNING
AREA: wordpress-qa
DATE: 2026-10-08
TYPE: LEASE
OWNER: chatgpt
SUPERSEDES: test-hub/findings/20261008-2237-lease-wordpress-extreme-plugin-qa.md
RESOURCES: UniversoAnthares/anthares-wordpress (all plugin code, QA/CI only; no production publication)
LEASE_UNTIL: 1791517800

PROGRESS: repository-wide lint and custom static QA are green on GitLab QA branch. The audit is continuing through public AJAX/REST callbacks, payment/webhook authentication, filesystem operations, duplicate symbols, diagnostic residue, and WordPress.Security sniffs before any application-code fixes are finalized.
SUCCESS_SIGNAL: all plugin roots inventoried; PHP/JS syntax clean; zero critical custom-static findings; evidence-backed security defects corrected; remaining heuristic findings manually classified; final GitLab pipeline green; closure recorded in Test Hub.
FAILURE_SIGNAL: any unresolved syntax error, exposed credential, missing static include, unauthenticated state-changing endpoint, path escape, or unexplained duplicate active symbol.
TEST_VALIDITY: every scanner must print file counts and run against a fresh branch checkout; infrastructure/config failures are invalid tests rather than product failures.
