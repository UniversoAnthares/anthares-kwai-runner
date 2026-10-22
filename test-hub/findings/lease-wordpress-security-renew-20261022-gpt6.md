# Renovação do lease — WordPress segurança da Aula 01
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
LEASE_OWNER: chatgpt-gpt6-wordpress-security
LEASE_EXPIRES_UTC: 2026-10-22T17:14:00Z
SUPERSEDES: test-hub/findings/lease-wordpress-security-20261022-gpt6.md
BASELINE_PROVEN: GitHub WordPress PR #65 branch 7a4a7dd, Hostinger PHP 8.4 CLI lint three PHP files passed and standalone smoke=PROVEN; live WordPress target file SHA256 match GitHub main originals. GitHub Actions job 119952698722 ended failure with logs unavailable; QA orchestrator has pre-existing and newly unassigned audit manifests.
FAILED_AVOIDED: do not rerun quota-limited hosted CI solely to discover quota; preserve production and protected main.
SUCCESS_SIGNAL: strict PHP lint + isolated smoke, GitHub/GitLab source truth preserved, live deployment with SHA verification and reversible backup if safely possible.
FAILURE_SIGNAL: tests fail, production baseline mismatch, deployment inaccessible, schema incompatible, or shared publisher conflict.
TEST_VALIDITY: no publication or customer data mutated as audit probe. External CI failure is not a test failure without decisive logs.
