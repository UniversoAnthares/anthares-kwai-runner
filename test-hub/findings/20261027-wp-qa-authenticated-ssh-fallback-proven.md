# CORTES WordPress QA — authenticated SSH fallback validated
STATUS: PROVEN
AREA: wordpress-qa-auth
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40501674442
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40501674442/job/122180625140
COMMIT: cd59ceba9303572e5f604ead0432934f4685fd90
SUPERSEDES: 20261027-lease-wp-auth-restoration-chatgpt.md

## Baseline, failure avoided and acceptance
BASELINE_PROVEN: The REST API `/wp-json/anthares/v1/cortes/state` correctly returns anonymous 401. Independent QA Windows runner does not receive GitHub repository secrets `WP_SITE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`; those missing references were confirmed by run 40499620554 and run 40501674442.
FAILED_AVOIDED: no anonymous bypass, copied credentials, new login, or retry after configured HTTP 401/403. Authorized hosting SSH `anthares-hostinger` already exists on the QA runner, and PHP 8.3 WP-CLI works where default PHP 7.4 fails.
SUCCESS_SIGNAL: official one-time Actions run completed success, all **27 Python regressions** passed; production CORTES state read through `wp_state_from_authorized_hosting()` produced `CORTES_WP_QA_AUTH_SOURCE=HOSTING_SSH_READONLY` and `WP_QA_ROUTER_ACTIVE=PASS incidents=0`. Independent standalone fallback emitted `WP_QA_AUTH_RESULT=PASS_SSH_WPCLI_READONLY`.
TEST_VALIDITY: owned runner `Anthares-QA-P0-Windows-Independent` executed checkout, tests, read-only SSH / WP-CLI, and ended SUCCESS. No issuer API writes, publishing, remote mutations or new authentication token.

## Scope
The existing P0 scanner `tools/cortes_qa_p0_router.py` uses the new fallback **only when API credentials are missing**, on the exact independent runner. It refuses any SSH fallback after an explicit configured REST HTTP 401/403, preventing privilege escalation from an auth denial. SSH key verification is mandatory; errors are sanitized and fail-closed. Parser and alert dedupe remain unchanged.

## Remaining limitations
Application Password REST authentication is still AUTH_MISSING and requires separate credential provisioning. The fallback is tied to the authorized Windows independent runner and SSH alias. Its availability on another machine/service is unverified. This is a proven bounded read-only QA source, not permission for publication or privileged WP changes.
The temporary one-time workflow is deleted from this branch before integration; existing QA schedules remain unchanged.
