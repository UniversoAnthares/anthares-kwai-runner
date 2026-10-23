# WordPress native personal-data exporter for Anthares PIX own tables — live checkpoint
STATUS: PROVEN for deployed source / scoped isolated tests; live data export END-TO-END NOT TESTED
DATE: 2026-10-23 America/Campo_Grande
AREA: WordPress/security/privacy ONLY
OWNER: GPT6 WordPress-security
LEASE: test-hub/findings/lease-wp-pix-privacy-exporter-20261023.md
GITHUB_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/76 (merged)
GITHUB_MERGE: 5db3e5e400cb6f0ca00616abb90b7f5d1e55baa4
GITLAB_MIRROR: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/commit/688b3c1bccb7e3a3eeae048e33d0105370843c00
TIME_LIMIT: 06:00 2026-10-23 America/Campo_Grande

## Precise gap
- Static search GitLab project 87361776 WordPress own code for wp_privacy/personal_data/privacy_export/exporter/eraser found zero existing proprietary export hooks.
- Static inspection on Hostinger of live anthares-pix-sales and mu-plugins found zero prior privacy exporter or eraser registrations. Dynamic enumeration of hook callbacks via WP CLI had been rejected by tool safety settings in earlier iteration and was NOT retried or bypassed.
- Installed WooCommerce registers 4 exporters/4 erasers for Woo-owned customer/orders/downloads/tokens; own tables are not Woo native order tables.
- Own table schema in anthares-pix-sales/includes/01-ativacao.php (unchanged): anthares_pix_orders includes buyer_name, buyer_email, buyer_cpf, payment_id, token, file_path etc; anthares_subscriptions includes payer_email, preapproval_id. Scoped exporter integration is justified, but does NOT prove legal compliance.

## Changed files, source ownership, hashes
1. anthares-pix-sales/anthares-pix-sales.php -> Git blob ab11a0f8d1c0da3d22fa7150525a1a8d0ad9a5c0. Version bumped 1.0.97 -> 1.0.98; guarded is_file/require_once so plugin boots if new module is delayed in deployment. Previous Git blob 27f6e7647579d5fc9f2b5bd6b81ffb49b414b3ae.
2. anthares-pix-sales/includes/96-privacy-export.php -> blob a43d042c6a64eb778bf29538eb0b293ec3ee4a44. New WordPress wp_privacy_personal_data_exporters callback; scope user_id of WP registered user resolved by verified email only, NO email-only table association or guest user_id=0. SQL placeholders for uid/limit/offset and bounded 50-item pagination per table per call. Minimal data fields: date/status/product/amount for orders; date/status for subscriptions. No select or disclosure of buyer_cpf, buyer_email, payer_email, payment_id, preapproval_id, token, private paths; no logging personal data. A failed DB lookup returns generic WP_Error, never silent success. No eraser registered.
3. tests/security-pix-privacy-export.php -> blob 676e665e2e546d1aa8b4202dd192aad0eea25026. 20 isolated assertions, 2 fictitious accounts IDs 101 & 202 plus guest/conflicting email fixtures, 54 fictitious orders Alice paginated 50+4 and 3 fictitious subscriptions, other user records protected, stable paging, no duplicate items, private fixture values absent, preserved Woo native exporter, zero deletion handlers, startup guard, invalid email short circuit, generic WP_Error on failed query.
4. anthares-pix-sales/PRIVACIDADE-EXPORTACAO.md -> blob 84e6ebd5445c77245b3700733ad329a7f41b2b3d; operations/config vs code, guest manual review and financial retention separate.
5. .github/workflows/wordpress-security-gate.yml -> blob 22c2011b1f888e3b03b1eb3bbcb51a53dc14ed8b; new files added to lint/unit gate, existing jobs preserved unchanged otherwise.
All five GitHub main files compared byte-identical to GitLab main after sync.

## Tests and live verification
- Local Windows isolated PHP 8.4.27: 3 PHP lint PASS, 20/20 unit assertions PASS with fictitious data; no real DB or payment connection.
- Hostinger CLI PHP 8.3.35 isolated under HOME (not public_html): same fixtures 20/20 PASS and lint PASS. This does NOT patch the vulnerable hosting runtime.
- No real user orders, subscriptions, token or CPF used. No payment processed. No live privacy request or erasure triggered.
- GitHub PR #76 merged; GitLab mirror commit includes only the five scoped files. Live Hostinger after automatic deploy was EXACTLY:
  - anthares-pix-sales active, version 1.0.98
  - plugin main blob ab11a0f8d1c0da3d22fa7150525a1a8d0ad9a5c0
  - exporter blob a43d042c6a64eb778bf29538eb0b293ec3ee4a44
  - live module php -l PASS.
- HTTP smoke homepage 200, /minha-conta/ 200, /enviar-capitulo/ 200, private REST /wp-json/anthares-campos/v1/health 401. No server-side error observed in these probes.
- Manual SCP rollout plan recognized both files already deployed and did NO overwrite. Source prior plugin v1.0.97 recovered from old GitLab commit, staged and private rollback file created outside public_html, SHA 27f6e7647579d5fc9f2b5bd6b81ffb49b414b3ae, mode 600.
- Remote GitHub combined status showed Vercel FAILURE due account build-rate limit. Do not present remote CI as green: isolated PHP proof is green; Vercel build did not validate this change.

## Guardrails and residual
- Guest orders and deleted users lack unambiguous WP user_id attribution; DO NOT export automatically by email-only. Operator must verify ownership separately; no new process was invented.
- No removal/anononymization, and no financial retention rules changed. Legal and accounting decisions remain separate.
- WordPress/WooCommerce existing Exportar Dados Pessoais interface reused. A live authenticated UI or dynamic callback enumeration was NOT performed; earlier WP CLI attempt blocked by security policy, not circumvented. Production proof is loaded PHP file + plugin version + HTTP health, not an actual live export.
- Other WordPress legacy custom table/plugin data is outside scope, no universal LGPD compliance claimed.
- Hostinger PHP 8.3.35 (patched 8.3.36+ needed), isolated full restore, ACF browser-level editing remain separate pre-existing issues.
- The playlist #21 ISO15408 remains blocked/pending. #22 is last actually reviewed. No CORTES, publishers, agent windows or runners changed; no extra monitoring automation created.
