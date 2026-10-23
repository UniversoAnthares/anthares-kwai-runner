# Hostinger PHP syntax test repaired and proven on live files
STATUS: PROVEN
AREA: wordpress-security
DATE: 2026-10-22
RUN: Anthares Remote Cloudflare SSH (noninteractive) job facb3bc868e227b9f2306de3c5c6e16e; earlier one-off a98fe0d018dec06ecb1377ff43d24cd8
JOB: facb3bc868e227b9f2306de3c5c6e16e
COMMIT: GitHub UniversoAnthares/anthares-wordpress main e852533ef0302913b63439532143cb00189e4a86; GitLab main fe4a7d1eb9d042e80f44b0ea0c75edf4e8d69b8d
SUPERSEDES: test-hub/findings/20261022-2204-lease-hostinger-php-lint-shell.md

## Root cause and correction
The original orchestration attempted Python subprocess.run(capture_output=...), unavailable in the old Python interpreter on Hostinger. An intermediate Bash attempt used stdin /dev/fd process substitution, also unsupported in that SSH/shell execution mode. Both were harness failures, not PHP syntax errors.

## Verified correction
qa/hostinger-php-syntax.sh (identical GitHub/GitLab content; SHA blob 6be704af6d382ba059a98628f22c4363afa177f7) uses pure Bash, a temporary null-delimited file inventory and trap cleanup, no Python and no process substitution.
Tested exact script source over authenticated SSH against live Hostinger WordPress installation. Output:
PHP_LINT_TOTAL=382
PHP_LINT_PASSED=382
PHP_LINT_FAILED=0
PHP_LINT_CLI_VERSION=8.3.35
WORDPRESS_PHP_LINT=PASS
REMOTE_EXIT=0
A separate one-off direct PHP lint also gave 382/382 PASS and exit 0.

## Limitations
A PHP lint test proves syntax only. PHP runtime remains 8.3.35 and host runtime security update remains a separate unresolved issue. No WordPress content or configuration was changed by this read-only lint test; no GUI windows opened.