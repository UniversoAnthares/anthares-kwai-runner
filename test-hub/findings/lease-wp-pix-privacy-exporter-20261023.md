# Lease: WordPress native privacy exporter for own PIX tables
STATUS: ACTIVE
DATE: 2026-10-23 02:28 America/Campo_Grande
OWNER: GPT6 WordPress/security/privacy only
SCOPE: UniversoAnthares/anthares-wordpress main, modify only anthares-pix-sales/anthares-pix-sales.php (blob 27f6e7647579d5fc9f2b5bd6b81ffb49b414b3ae), create includes/96-privacy-export.php and tests/security-pix-privacy-export.php, append CI gate in .github/workflows/wordpress-security-gate.yml (blob 585d7c1b697704f3935bf1608f1cbc6930a3f6ec). Peer GitLab main 954e62c786e9abd1f31a457795b0b777aaa4bfde, target contents same as GitHub at acquisition.
EXCLUDES: CORTES, publishers, agents, runners, payment state changes, removing/anonymizing rows, WooCommerce internals, credentials, private archives and Hostinger PHP.
BASELINE: Static GitLab full project search wp_privacy/personal_data/exporter/eraser returned zero own-source hooks. Static Hostinger grep under live anthares-pix-sales and mu-plugins returned no matching hook registrations. Installed WooCommerce has four exporters/erasers but not own custom PIX tables. Dynamic WP-CLI callback enumeration was blocked by tool safety settings in previous round; DO NOT evade it. Static evidence suffices to add scoped exporter, not claim full dynamic coverage.
GOAL: single WP native exporter (no eraser); prepared paginated read-only SELECT of two own tables keyed by identity, no exposure of buyer CPF, tokens, payment IDs, private file paths, emails or other-user records in logs/test reports.
GUARDS: Two fictional identities and guest samples, conflict and pagination adversarial test, 0 live financial actions. Read HEAD/target fresh before write and optimistic concurrency. Isolated PHP tests, lint, PR review, mirror GitLab only after source/check; verify live code hash before status claim; rollback retained.
PROOF: WP hook callback registered in fixture; positive registered/guest email cases and conflict exclusion, 2-page pagination with no duplicates, no private fields; site smoke. Do not certify legal completeness.
STOP: 2026-10-23 06:00 America/Campo_Grande.
