# WordPress security: XXE/IDOR/XSS live checkpoint and Lesson 11 review
STATUS: PROVEN for XXE/IDOR/XSS scoped checks; INCOMPLETE for deserialization hardening, provider PHP and full restore
AREA: wordpress-security
DATE: 2026-10-23 America/Campo_Grande
OWNER: GPT6-WordPress-security
PREDECESSOR: test-hub/findings/20261022-wordpress-acf-schema-audit-and-https-live-proven.md

## Production checkpoint
- XXE lesson #7: Hostinger anthares-pix-sales/includes/39-integracao-lucas-rosalem.php actual git blob 8e135dfb79c35eed3de03a434d1717f3336f059c matched GitHub main. Hostinger PHP 8.3 lint PASS. Isolated 11/11 tests PASS (good XML parsed, external entity/DTD/oversize/malformed refused, private provider body logging eliminated). No live YouTube post import invoked.
- IDOR lesson #8: Hostinger anthares-pix-sales/includes/05-ajax-pagamento.php git blob e69760e315e3c8cdeac71ad61f4b3b0b82dd22f0, PHP lint PASS. Existing request verifies order ID AND 40-character token via prepared SQL before provider call, plus provider identity and currency/amount. Six isolated negative/positive tests PASS; no real PIX transaction invoked. New tests merged GitHub PR 74 and mirrored GitLab commit 369972e2f22fe6f69cf9a6558fb7ab87a331258e. NO proof of every other payment endpoint.
- XSS lesson #10: source anthares-pix-sales/includes/38-youtube-importer.php previous live sha 5a3e8e3cfdbefba224afdb58aac4727a43aecc19. Fixed admin dashboard progress render escaping ALL dynamic AJAX values (message + counters + exception), avoiding dynamic HTML retry wrapper. Isolated 15 tests PASS and PHP 8.4 CLI lint PASS. GitHub PR 75 merged to 058b9ab3e992188d9368952ed1ef2deba54c7874; GitLab mirror fa7d750d2115a094621a28a8f8bf26a2f28dbad9. Hostinger later rechecked actual blob ef456fad71d7b93c1837bca8393f4de39a91ed73 and PHP 8.3 lint PASS. Plugin active. No authenticated browser UI clickthrough, and not a sitewide XSS guarantee.

## ACF and proxy
- ACF verified previously using WP-CLI under deliberately selected admin user context: five free field types read/write PASS on a disposable private QA post, deletion and remaining postmeta=0 PASS; 12 registered groups. This is NOT a real browser login/edit of each form.
- Four historical post types registered group location but no runtime post type: etapa_1, etapa_2, etapa_3, projeto_de_livro. No proof these were actively used.
- AIOS effective IP method 0 REMOTE_ADDR under Hostinger hcdn; normal request REMOTE_ADDR==X_REAL_IP==first XFF, and XFF spoof did not change REMOTE_ADDR or AIOS IP. No IP addresses logged; transient origin probe deleted. Login IP lockout still OFF; no mass lockout enabled.

## Lesson 11: Aula 04, Módulo 03 — Desserialização insegura
- YouTube: https://www.youtube.com/watch?v=XVepmG4mj7M ; full automatic Portuguese captions examined (approx. 23 min).
- Proportionate rule: verify MAC/signatures on stateless tokens; do not accept unsigned claims; disallow class instantiation when reading serialized data from uncertain sources. Avoid treating json_decode as equivalent to PHP object unserialize risk.
- Existing WordPress code searched for unserialize, maybe_unserialize, jwt_decode, JWT::decode, base64_decode. No custom JWT decoding identified in repository search. maybe_unserialize used in internal WordPress DB postmeta/usermeta paths (Anthares Assistente, Email Auto, XP weekly meta, PIX Sales Plus role), NOT proven reachable directly from unauthenticated input.
- Proposed minimal change for class loading from stored weekly XP metadata: file anthares-xp/includes/class-anthares-xp-meta-semanal.php, baseline GitHub blob 84d0c6386002955ca52231cd2cbc1de4caf2ed8a; read two maybe_unserialize sites. A proposed update was blocked by tool policy before writing. Neither GitHub main nor production code changed; branch security/lesson11-xp-deserialize-20261023 may exist but no PR or changed source. Do not declare hardened. Test target for a future permitted implementation: PHP serialized arrays remain functionally identical; crafted serialized object never invokes __wakeup; WordPress weekly metric counts unchanged.

## Lesson 9: hosting vs code vs backup
- Hostinger PHP 8.3.35 application and optional PHP 8.4.26 (not verified patched) remain a hosting/provider update, not a code patch. WordPress WP_DEBUG OFF, DISALLOW_FILE_EDIT ON; HTTP to HTTPS 301 confirmed, sensitive path probes 403.
- Private backup acf-pro-files-pre-replacement-20261022.tar.gz inspected by tar list: 297 entries, no absolute paths/../ traversal/symlink or hardlink entries according to tar -tvzf. Backup is only retired plugin files, not a full WordPress/site/database backup.
- Attempt to extract into an isolated outside-public_html directory was blocked BEFORE execution by tool security settings. No restoration was performed or claimed. Full recovery rehearsal stays unproven; use isolated staging only, never live production.

## Scope ownership
- This chat owns only WordPress security: source anthares-pix-sales/includes/38-youtube-importer.php, tests/security-lesson10-xss.js and additive CI gate changes. Source merged, tests passed, live blob verified. No CORTES code/publications/agencies/runners altered.
- XP deserialization proposed but NOT applied due tool block. Next unreviewed video: #12 Kb2PR2gKoww, components with known vulnerabilities (approximately 11m20).
- Existing hourly automation until 06h remains; do NOT schedule duplicate monitor.
