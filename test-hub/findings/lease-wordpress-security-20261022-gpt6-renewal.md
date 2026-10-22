# Renewal — WordPress security cross-platform regression
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
LEASE_OWNER: chatgpt-gpt6-wordpress-security
LEASE_EXPIRES_UTC: 2026-10-22T17:30:00Z
SUPERSEDES: test-hub/findings/lease-wordpress-security-20261022-gpt6.md
BASELINE_PROVEN: GitHub WordPress main 0db5db74ba7df5981798b08f694cb56d4a22953f; live ping version 1.0.8; portable PHP 8.4.27 lint passed on both bridges and test script.
FAILED_AVOIDED: PHP syntax QA script failed on Windows path normalization, not due to an access-control bypass. Test harness had Windows separators; fix absolute canonical path handling and rerun.
SUCCESS_SIGNAL: live-comparable source passes isolated PHP parser and functional smoke with WORDPRESS_SECURITY_LESSON01=PROVEN_SANDBOX.
FAILURE_SIGNAL: PHP lint error, unauthorized path success, backup visible inside web root, hashless write success.
TEST_VALIDITY: isolated Windows filesystem differs from Linux production; live check limited to read-only status and no test writes on live WordPress.
RUN: ARA detached job 78d7ab9be5e6203c, prior test failed at hashless editor assertion.
