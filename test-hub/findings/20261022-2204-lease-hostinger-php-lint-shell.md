# Lease: Hostinger PHP syntax QA without Python
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
OWNER: chatgpt-gpt6-wordpress-php-lint
LEASE_EXPIRES_UTC: 2026-10-23T03:10:00Z
BASELINE_PROVEN: authenticated read-only Hostinger SSH command using direct Bash and /opt/alt/php83/usr/bin/php; exact one-off remote job bb2ed6104f1a843ffaebccb99b7ea42a output PHP_LINT_TOTAL=382 PHP_LINT_PASSED=382 PHP_LINT_FAILED=0 REMOTE_EXIT=0.
FAILED_AVOIDED: Python subprocess.run(capture_output=...) unsupported by old interpreter; Bash process substitution via stdin absent /dev/fd/62.
OBJECTIVE: commit a reproducible Bash-only QA script that uses a real tempfile and trap, checks every anthares-* PHP plugin and returns nonzero on lint failure.
SUCCESS_SIGNAL: same real-host test using committed script; count >=300, failed=0 and exit 0; GitHub and GitLab content equal; independent HEAD preserved.
FAILURE_SIGNAL: no files, syntax error, mismatch, non-zero command, stale base.
TEST_VALIDITY: PHP parse check, not vulnerability or runtime PHP patch check. PHP 8.3.35 remains vulnerable until updated in Hostinger.
