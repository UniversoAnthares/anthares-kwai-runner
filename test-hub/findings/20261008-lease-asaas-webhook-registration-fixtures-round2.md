# Lease: Asaas webhook registration mock integration
STATUS: RUNNING
AREA: wordpress-payments
DATE: 2026-10-08
BASELINE_PROVEN: WordPress PR18 d71a349, GitLab 2927111773 success, six token mock tests.
FAILED_AVOIDED: no production Asaas request, no destructive webhook replacement, no PC runtime, no forced mirror.
SUCCESS_SIGNAL: hosted PHP tests validate existing provider webhook preserved, list failure no POST, no token no provider calls, missing webhook new registration.
FAILURE_SIGNAL: any duplicate webhook or unsafe POST on missing auth.
TEST_VALIDITY: isolated PHP fixture extracted from actual source, no provider network.
Scope: WordPress PR18 branch only; expiry 30 minutes.
