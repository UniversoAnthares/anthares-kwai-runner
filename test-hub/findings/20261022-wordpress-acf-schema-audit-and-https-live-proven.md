# ACF migration dependency audit and HTTPS headers production
STATUS: PROVEN
AREA: wordpress-security
DATE: 2026-10-22
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/71 and https://github.com/UniversoAnthares/anthares-wordpress/pull/72
COMMIT: GitHub main 7b320adbbf553cc7e4bcb1476988b02d118da6ad; GitLab main b6b442b023e775bfc7559373f014181f56aae1d3
SUPERSEDES: test-hub/findings/lease-wordpress-acf-dependency-security-20261022-gpt6.md
LEASE: CLOSED

## Verified
- Post-migration audit of Anthares Campos 1.0.0 and ACF free 6.8.10; legacy PRO remains inactive. 12 registered ACF groups, 33 fields, all five types available in ACF free (post_object 7, range 5, text 2, textarea 14, true_false 5).
- Explicit code calls: Anthares Home challenge gallery/archive images use get_field with fallback to postmeta (two calls). Anthares PIX Sales live-review queue uses update_field with postmeta confirmation (one call). Both compatible with free ACF.
- WordPress themes iknow and Customify have own namesake field accessor methods, not ACF. Third-party AIOSEO has optional ACF helper APIs guarded by function_exists for flexible content, but active ACF groups contain no flexible fields.
- Database count: 891 ACF reference postmeta rows over 207 posts. There are 46 obsolete field references across 23 published contos: _arquivo 22, _autor 22, _texto 1, _nota 1. Each reference still has the corresponding unprefixed stored metadata value, none changed or deleted.
- No ACF references in saved post_content blocks, zero in six Code Snippets rows and four WPCode posts. Scope is source/runtime scan, not exhaustive manual authenticated page editing.
- Added guard that checks field-type distribution and all expected 12 post-type group locations, warns on any PRO-only field or missing schema.
- PHP 8.4.27 lint for 4 files PASS; ACF regression 8 cases PASS; HTTP headers regression 13 cases PASS.
- Security headers active in WordPress, short HSTS max-age=86400 (no includeSubDomains or preload), nosniff and referrer minimization. Initial REST gap fixed via rest_pre_serve_request; production PHP code blob b21bb4f160d684e480b65a9fd4c8a40470a2a154 lint PASS.
- HTTPS smoke shows homepage/login/account 200 with HSTS and nosniff, private REST health and CORTES REST 401 with HSTS and nosniff, public bridge REST 200 with HSTS and nosniff. Challenges, chapter-upload and account pages each 200.
- Five changed files verified byte-identical between GitHub and GitLab.

## Limitations kept open separately
- Hostinger PHP 8.3.35 is not patched; requires hosting runtime update.
- AIOS 5.4.10 is active but login lockout and brute-force setting switches are empty/disabled. Deliberately not enabled without confirming actual client-IP attribution behind proxy; avoid shared-IP lockouts.
- Legacy field references remain intact; no schema rewrites. No claim that all private editors were manually browser-tested or that all website security defects were removed.
