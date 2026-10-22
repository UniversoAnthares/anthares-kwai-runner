# Lease WordPress legacy backup and PHP runtime monitor
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
OWNER: chatgpt-gpt6-wordpress-safesource
LEASE_EXPIRES_UTC: 2026-10-22T18:15:00Z
BASELINE_PROVEN: live PHP/8.3.35; WordPress filebridge 1.0.9; old legacy backups in WP_CONTENT_DIR/wp-content/backups or WP_CONTENT_DIR/backups. PHP patched thresholds from php.net 2026-10-21.
FAILED_AVOIDED: do not misclassify the historic doubled wp-content path as wrong. Preserve BOTH layouts. Never touch unexpected/symlinked files. Prevent repeated mail via bounded throttle.
SUCCESS_SIGNAL: sandbox verifies both historical backup locations quarantined preserving hashes; threshold table accurately classifies 8.2.35,8.3.36,8.4.27,8.5.12; dashboard and daily alert are registered; current PHP still marked vulnerable; PHP lint passes; live uses new plugin version.
FAILURE_SIGNAL: backup corrupted/exposed, regression suite failure, wrong PHP version classification, alerts repeated within 24h.
TEST_VALIDITY: artificial runtime samples only verify guardian; real PHP remediation requires Hostinger control and updated live version evidence.
