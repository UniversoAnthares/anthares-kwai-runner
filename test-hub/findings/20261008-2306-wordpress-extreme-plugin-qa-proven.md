# PROVEN — WordPress extreme plugin QA
STATUS: PROVEN
AREA: wordpress-qa
DATE: 2026-10-08
TYPE: FINDING
OWNER: chatgpt
SUPERSEDES: test-hub/findings/20261008-2249-lease-wordpress-extreme-plugin-qa-renewal.md

SCOPE
- Repository: UniversoAnthares/anthares-wordpress
- Final GitLab main commit: b0c6cf63f8a75ca71c4d8c5c1e25dc35fc64f4be
- Merge request: !17
- Main verification pipeline: 2928884357 — SUCCESS
- Full audit branch pipeline: 2928877088 — SUCCESS, 5/5 jobs
- Plugin inventory: 15 Anthares roots; 323 plugin PHP files; 37 JS files; 449 code assets scanned.
- Repository-wide PHP lint: 328 PHP files, failed=0.
- JavaScript syntax: 37 files, failed=0.
- PHPCompatibilityWP, PHP 8.1–8.4: files_with_findings=0, errors=0, warnings=0.
- Custom static QA: critical=0, warnings=13, info=4. Remaining warnings were manually classified; none represented a demonstrated reachable critical defect after review.

QA COVERAGE
- PHP syntax and JS syntax.
- PHP 8.1–8.4 compatibility.
- WordPress.Security PHPCS inventory and priority triage.
- Embedded secret/private-key patterns.
- Merge-conflict residue.
- Static include/require targets.
- Duplicate prefixed global functions/types and duplicate literal hook registrations.
- Public AJAX and REST endpoints.
- Payment/webhook authentication for Mercado Pago, Asaas and Telegram flows.
- Upload handlers and private-storage paths.
- Direct output from request superglobals.
- SQL calls near request superglobals.
- Dynamic include patterns.
- eval/shell/system/exec/unserialize families.
- Redirects and external HTTP/cURL call sites.
- save_post mutation callbacks and nonce/capability guards.
- Diagnostic/self-test residue and plugin-header hygiene.

FIXES INTEGRATED
1. Deleted legacy duplicate `anthares-wpvibe-filebridge/anthares-wpvibe-filebridge.php`. It exposed unrestricted ABSPATH-relative list/read/write behavior behind a broad manage_options gate and leaked filesystem paths through public ping; no repository references depended on it. The constrained root `anthares-wpvibe-filebridge.php` remains.
2. Hardened `anthares-pix-sales/includes/53-convites-desafio.php` video-meta saving with a dedicated nonce, revision/autosave guards and `edit_post` capability verification.
3. Added `qa/anthares-extreme-static-qa.php` and persistent GitLab QA for repository inventory, PHP lint counts and JS syntax. Security and compatibility audit jobs remain reproducible on qa/* branches with artifacts.

MANUAL CLASSIFICATION
- AI Bridge `exec()` is limited to escaped PHP binary + escaped temporary file for `php -l`; command arguments are not user-controlled shell fragments.
- Lovecraft admin AJAX uses a shared request validator with nonce and manage_options capability.
- Public provider webhooks use signatures/tokens and provider-side reconciliation before finalization.
- Public TikTok OAuth callback validates signed expiring HMAC state; worker REST routes require the configured worker secret with hash_equals.
- Public Home origin/referrer AJAX uses dedicated nonces and constrained state.
- Reviewed uploads enforce login/capability/ownership or management access, extension/MIME/size constraints as applicable, randomized names and private storage where sensitive.
- WPCS priority warnings caused by helper-mediated nonce validation, safe checked array access, provider callbacks or trusted fixed redirects were retained as audit evidence rather than changed without a demonstrated defect.

INFRASTRUCTURE NOTE
GitHub Actions runs 37858681000 and 37835315016 terminated before runner execution (`runner_id=0`, `steps=[]`), so they are invalid execution evidence. GitLab hosted runners supplied the reproducible QA evidence. This infrastructure limitation does not reduce the successful GitLab code-audit result.

LEASE: CLOSED
