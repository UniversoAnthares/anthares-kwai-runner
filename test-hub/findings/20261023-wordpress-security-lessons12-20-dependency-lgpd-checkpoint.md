# WordPress security lessons 12-20 — 2026-10-23 checkpoint
STATUS: READ-ONLY AUDIT PROVEN; NO NEW CODE OR PRODUCTION PLUGIN UPDATE IN THIS ITERATION
OWNER: GPT6 WordPress security (not CORTES/clipper, publishing, runners, agents)
PREVIOUS: test-hub/findings/20261023-wordpress-security-xss-deserialization-checkpoint.md
LAST ANALYZED: #20 vnA1B-STqAs, Aula 07 Módulo 03 LGPD
NEXT UNANALYZED: #21 5rHrWm1fcv0, ISO 15408/Common Criteria; after that #22 NhdrUPViYDk.
DEADLINE: 2026-10-23 06:00 America/Campo_Grande. Existing hourly automation already scheduled; do not create another.

## Lesson 11 deeper trace (no change)
Class file anthares-xp/includes/class-anthares-xp-meta-semanal.php GitHub main SHA 84d0c6386002955ca52231cd2cbc1de4caf2ed8a, GitLab byte-identical.
- XP weekly current meta key anthares_xp_meta_semanal_atual written ONLY in method carregar() via update_user_meta() lines 1019/1082 from canonical XP/eligibility catalogue.
- Week archival meta key anthares_xp_meta_semanal_historico written in arquivar() via update_user_meta() line 944; both values expected arrays. Internal metric reports read them via maybe_unserialize() on rows 1297 and 1353.
- Admin calibration method has manage_options plus nonce, modifies separate calibration options, not arbitrary serialized bytes. No discovered route directly letting an untrusted client post serialized PHP bytes into those usermeta keys. User activity influences goal selection, not serialized payload.
- No demonstrable exploitation path. Do not globally replace WordPress maybe_unserialize, and do not assert a hardening patch: previous attempted patch blocked by tool security before writing. Residual risk noted. If future proof finds exposed untrusted writer, local patch plus isolated array/serialized-object no-method-execution test.

## #12 Uso de componentes vulneráveis
Video https://www.youtube.com/watch?v=Kb2PR2gKoww — complete Portuguese captions analyzed.
WP-CLI active versions: core 7.1.3, AIOS 5.4.10, Elementor 4.3.5, WooCommerce 11.2.1, Jetpack 16.3.1, WP File Manager 8.0.6, Advanced File Manager 6.0.0, AIOSEO 5.0.3. Patchstack/vendor confirmed those versions meet recent listed patched minima, NOT universal assurance.
WP CLI updates offered: AIOSEO 5.0.4; MercadoPago 8.9.7; WPForms 2.0.3; WP Mail SMTP 4.10.3. No published version-applicable exploitable CVE proved for these current installs and package provenance/changelogs can differ: avoid cosmetic unsafe updates or checkout regressions until vendor authenticity, staging, rollback and smoke validated.
Confirmed vulnerable PHP hosting runtime: web/CLI 8.3.35 and alternate 8.4.26 below fixed 8.3.36/8.4.27 for CVE-2026-109618/109619. Dependency belongs to Hostinger, not WP PHP code. Source https://cert.europa.eu/publications/security-advisories/2026-018/ .
Relevant plugin advisories: https://patchstack.com/database/wordpress/plugin/elementor/vulnerabilities , https://patchstack.com/database/wordpress/plugin/woocommerce/vulnerabilities , https://patchstack.com/database/wordpress/plugin/jetpack/vulnerabilities , https://wordpress.org/plugins/wp-file-manager/ .

## #13 Registro e monitoramento insuficientes
Video https://www.youtube.com/watch?v=7NOH98txQko — complete captions analyzed.
Existing AIOS table wp_aiowps_audit_log has 4592 events (3895 failed_login, 244 successful_login, 110 plugin_updated, 99 plugin_activated, 59 plugin_deactivated, 55 plugin_installed, 46 plugin_deleted); range 2026-07-25 to 2026-10-22. Last 24h query: 1 failed and 1 successful login, 0 plugin-change events. All queries grouped, no username/IP/details printed. Existing logs are evidence but do not establish exhaustive event coverage, retention policy or prompt review. DO NOT install duplicate collector/monitor. Use existing QA cadence if testable.

## #14 Buffer overflow
Video https://www.youtube.com/watch?v=XKGIYV68nns — native C/C++ issue: no evidence of custom WordPress direct native buffer manipulation; PHP host interpreter critical RCE via memory corruption is actual issue. Do not pretend PHP code can replace ASLR/stack canaries. Fixed PHP runtime plus web smoke required.

## #15 Outros ataques a aplicações locais
Video https://www.youtube.com/watch?v=vkhvFZqa2Xc. Browser/client is untrusted; existing PIX checks server side order ID and secret per-order token (#8 test, six cases). Obfuscation is not an auth measure. Audit absence of exposed permanent secrets in browser JS separately; no known native APK vulnerability proved in WordPress scope.

## #16 and #17 Practice and answer key
#16 https://www.youtube.com/watch?v=rgaFE32zyjQ ; #17 https://www.youtube.com/watch?v=sykGZvdBIE8.
Old video creates deliberately insecure DVWA using obsolete PHP 5.6 and weak credentials, bridged network. Do NOT install in live WordPress or connected Windows host. Use isolated disposable fixtures only. Existing PHP/JS negative tests for XXE/IDOR/XSS are evidence for their scoped flows; NOT site-wide SQL injection certificate.

## #18 PCI-DSS
Video https://www.youtube.com/watch?v=IrKv_0IPPj8. Own repo source search for cvv/cvc/card_number/cardNumber/cardToken/card_token/cardholder/pan_number found 0; this does NOT cover vendor WooCommerce gateways or prove no card data processed. Confirm actual checkout redirect vs iframe vs direct-post architecture before assessing SAQ scope. No PCI DSS certification. Do not store CVV after authorization even encrypted. https://www.pcisecuritystandards.org/faqs/1319/

## #19 PA-DSS
Video https://www.youtube.com/watch?v=MzLNuL9MLMQ. Historical PA-DSS retired 2022; Secure Software Standard and Secure Software Lifecycle superseded it: https://www.pcisecuritystandards.org/standards/pa-dss/ . Relevant principle: source control, patch provenance, secure changes, test and rollback, no real payments as test artifacts.

## #20 LGPD
Video https://www.youtube.com/watch?v=vnA1B-STqAs. WP privacy page configured as post ID 3, published and HTTP 200 at https://anthares.us/politica-de-privacidade/ . Own repository search found no explicit central LGPD/privacy_erasure/data_export/delete_account symbols, but WordPress/WooCommerce may have native APIs; do not declare absent without inspection. Consent is not universal basis; children's data has legal alternatives subject to best interest, small processors can have DPO exceptions, significant-risk incidents typically 3-business-day notice under ANPD regulation. Sources: https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes and https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis . Criterion: data inventory and legal basis, personal data retention, verified export/correction/deletion and incident response; NOT fully proven.

## Blocker and next
Request to fetch captions for #21 via Anthares Remote returned explicit tool security block BEFORE execution. No bypass attempted, so #21 remains UNANALYZED. Existing authorized hourly automation should consult this checkpoint; no new monitors, no blind deploys. No production patches or user records altered in this round.
