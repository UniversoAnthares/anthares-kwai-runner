# Anthares Studio / PR #417 — release audit

Date: 2026-11-23 America/Campo_Grande. Owner: GPT6/STUDIO_ITEMS_1_3_4_7_8_11_14_16_17.
Related lease: test-hub/findings/lease-studio-comments-follows-retention-structure-20261123.md.
Repository: UniversoAnthares/anthares-wordpress; PR #417 squash merged into main adccf62e664e13a45c9fdd7fa18cf22fc90693d2.

## Published code
1 Comments: author controls independent view and accepting new comments; protect administrator and anthares root and replies from direct user deletion. Hard delete entire eligible comment tree in wp_comments/wp_commentmeta, and purge orphan threads on same-edition edit or later publication when original paragraph removed. Physical SQL verified.
3 Follows: authors of native Contos pending, published or anth_beta, editorial blog and Studio; user meta persistent; follow/unfollow idempotent. 4 Bell alerts on published contos/posts/Studio chapters, no alerts after unfollow.
7 Reading reports: new hidden author-only subpage #studio/projeto/{id}/relatorios linked from Analyses and publication; bars for 10/25/50/75/90/100% and privacy threshold server enforced.
8 Every nine registered narrative models accepts chapter drag/drop; new chapters in stage; chapter rectangles projected at selected stage percent on permanent three-act ruler with accessible list and manuscript jumps.
11 Character appearances by names/aliases and confirmation existed and passed real WP QA.
14 Editorial tips from WordPress Dicas de Escrita existed and passed real WP QA.
16 Collaborations via private beta invitation: explicit author consent transfers offered Runas upon approval to reader with atomic duplicate-proof dual ledger. Site-funded 1 Runa for approved public beta feedback remains independent. BRL bank settlement not available and pending. 17 Mentor invites, acceptance, private structured feedback and revocation tested.
Urgent list: preserve ids, remove 2,5,6,20, earlier 15 already absent, leaving 19 entries, Style item21 pending; general historical inventory PENDÊNCIAS.md preserved.

## QA
WordPress real post-deploy, all InnoDB ROLLBACK=EXECUTED: comments 35/35, following 34/34, Runa wallet 9/9, mentoring 9/9, follow notices 33/33, retention 9/9, tips 21/21, structure models 46/46, character appearances 28/28. SUM 224 / 224.
Python static contract: narrative timeline 12/12, reading report 3/3, story domain 21/21 PASS.
JS V8 syntax: six changed scripts PASS. Manifest 768/768 exactly once.
Private CAS deploy: ten existing production plugin files checked against previous GH blob hashes, one new asset installed. First CAS attempt aborted because stage branch was one commit behind; second backup preparation aborted before production change due root-level file directory; fixed private backup and performed final deploy with matching GH blobs. Release result PR417_DEPLOYMENT_OK.
Private backup: /home/u566597497/domains/anthares.us/studio-private-backups/20261123-studio-items-1-3-4-7-8-11-16-17-pr417.
Public CDN readback SHA matched: comments.js ced060d82a8f524b2d7b60fbd1a6abac3c1d66c8; estudio.js 91294ce544f9db50b91cb12e7f582871a0b2197c; timeline.js 2761cfee18c0e440c1744c52f3c668c1380eae11; reports.js 31aa8841103302a486b592fbc6b6da88911ebc87; publishing.js 634e4547eb31df830ea0195290a315720aaa547e; beta-author.js 70bf3ffbf01d3111f6268a80313133e1034dd659. /studio HTTP200 and /estudio HTTP200, legacy hash e4a9812ac21b5c977b93e53fe65131b43e23ba85.

## Remaining
Authenticated manual visual browser and mobile QA across real writer/reader/mentor accounts, long text, paragraph edit/publication changes and concurrent writers (urgent item23).
Author-funded BRL disbursement requires a verified authorized external payout provider and reconciliation; do not infer that pending obligation is paid.
Graph of Style (urgent item21) remains pending editorial definition; 188-feature matrix (urgent item24) still needs current evidence.
Private deployment stage remains for controlled audit; backup must be retained.
