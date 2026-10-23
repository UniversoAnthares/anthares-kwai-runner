# WordPress ACF dependency and lessons 04-06 security implementation lease
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
OWNER: ChatGPT-GPT6
LEASE_EXPIRES_UTC: 2026-10-23T03:49:00Z
BASELINE_PROVEN: ACF PRO disabled, Anthares Campos 1.0.0 plus ACF free 6.8.10 active and 12 groups, 33 fields. GitLab main ba389c41cea9dce6b79e556118ff878cefeed4e1. Read-only Hostinger DB: 891 field references in 207 posts; 46 stale references in 23 published contos; no ACF shortcode/block in content; 0 active code snippets using ACF.
FAILED_AVOIDED: do not rerun broad remote base64 shell after security denial, do not touch historical ACF post_meta or overwrite pages, avoid PHP 7.4 CLI by using alternate 8.3 path; do not disable free plugin or interact with credentials.
SUCCESS_SIGNAL: scoped plugin regression detects drift; exact unchanged ACF data; live HTTPS headers checked with rollback; SQL/XSS/auth protection implemented only if no duplicate.
FAILURE_SIGNAL: lost 12 groups/33 fields, WordPress fatal, changed private data, unverified deployment, diverged GitLab files.
TEST_VALIDITY: server count/static checks do not prove every authenticated page form; keep that limitation explicit.
