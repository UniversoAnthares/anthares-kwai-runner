# Lease — Implementação dos módulos 02/03 no WordPress
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
OWNER: chatgpt-gpt6-wordpress-lesson02-03
LEASE_EXPIRES_UTC: 2026-10-23T03:08:00Z
BASELINE_PROVEN: GH main reviewed AGENTS.md; GitLab main fe4a7d1eb9d042e80f44b0ea0c75edf4e8d69b8d; filebridge production version 1.0.10, PHP 8.3.35; previous standalone security regression proven.
FAILED_AVOIDED: avoid edits without baseline SHA; avoid forced synchronization of divergent histories; avoid payment/provider live side effects in tests; avoid Windows visible sessions.
SUCCESS_SIGNAL: isolated PHP lint/test suite PASS; two providers source equality per changed path; real WordPress endpoint still healthy; corrected callbacks require consistent identifiers and published proof; source deletion can never cross canonical uploads path; private uploads validated; CI paths cover changes.
FAILURE_SIGNAL: syntax error, inconsistent peer merge, production 5xx, invalid authorization, erroneous deletion or breaks payment test.
TEST_VALIDITY: synthetic callbacks are distinct from real external publication; no money transfers in automated tests; Hostinger PHP runtime patching is separate and only PROVEN by live handler version.
