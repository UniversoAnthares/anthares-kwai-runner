# Scope lease — WordPress security, ACF auth QA and security lessons 07+
STATUS: RUNNING
OWNER: GPT6 ChatGPT
DATE: 2026-10-23 America/Campo_Grande
AREA: wordpress-security
SCOPE: wp-content/plugins/anthares-fields, anthares-security-headers, test-only ephemeral diagnostic scripts outside public_html and their test runners, site security configs only after proven safe.
EXCLUDES: all CORTES clipper/publishers, queues, agents and Git runners; another chat owns them.
BASELINE: GitHub Anthares WordPress AGENTS.md freshly read; GitLab main 4c52a2e772f43601397d921bf2aabfa45c408a10 at start; ACF 12 groups/33 fields in free engine, old PRO inactive; HSTS 86400 and REST headers deployed.
OBJECTIVES: authenticated-capability ACF reversible write/read for all five field types on disposable private QA post; no lasting postmeta; determine true client IP handling behind proxy before lockout; study playlist videos from #7, record exact titles, minimal mapped recommendations with tests; verify source ownership before patches.
STOP: date deadline 2026-10-23 06:00 America/Campo_Grande or tool hard blocker.
GUARDS: do not touch real user posts/fields, production money or live publisher; no secrets in logs or commits; no broad lockouts; cleanup all owned temporary files/windows.
SUCCESS_PROOF: WP CLI security context + read/write results and cleanup, IP proxy raw relation or UNCERTAIN, plugin tests + real HTTP 200/401, unique video IDs with evidence, hash verified commits.

FILE OWNERSHIP FOR THIS ITERATION (2026-10-23 01h): GPT6 WordPress-security owns only `anthares-pix-sales/includes/38-youtube-importer.php` XSS-safe admin display, new `tests/security-lesson10-xss.js`, and append-only testing lines in `.github/workflows/wordpress-security-gate.yml`. No editing other parts of PIX, CORTES, queues, automation or shared agents. Re-read target hashes before mutation. If another owner modifies these targets first, abort/reconcile instead of overwriting.
