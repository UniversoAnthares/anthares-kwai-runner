# Anthares Studio — G4 backend funcional e restauração WordPress homologados
STATUS: PARTIAL
AREA: studio-g4-backend-regression
DATE: 2026-11-16
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: g4-backend-isolated-20261116
LEASES_CLOSED: test-hub/findings/20261116-studio-g4-regression-lease.md, test-hub/findings/20261116-studio-g4-restore-hotfix-lease.md
CODE: anthares-wordpress PR #310 (draft), SHA dbf739b32ddd3e8f6cbb11f98f196713fd1d8612
LIVE_PHP_SHA256: 477f4e2dd2fe1cc79c0f0793109c257edb212d0e16e68f68c3278d323233a7b3
PREVIOUS_LIVE_PHP_SHA256: be660f3e18bea5b227d415816098cab9c7c8f39fdaa31b31f718055f4d698243
LEGACY_PHP_SHA256: 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf
BACKUP: Hostinger private storage studio-g4-restore-hotfix-20261116/old.php (mode 600), rollback validated by manifest.

## Isolated G4 REST regression (PASS)
- WordPress database snapshot (sha256 26369c846d50ca691bf53423171a385cc7fe782b829f401a4bf859fff230b688) restored to MariaDB isolated UNIX socket, --skip-networking.
- Clone plugin from PR #310, original plugin left untouched.
- REST creates/updates project, note, chapter and card (HTTP 200). Stores Quill Delta with Unicode and formatting, decoded read equals written Delta.
- Author A can see four created entities via bootstrap, author B cannot edit (404) or see author's new project in their own bootstrap.
- Delete item to trash and restore: WP returns 200 and post_status returns publish; item appears again in bootstrap.
- Changing anst_writes_enabled back to 0 makes POST return 423.
- Isolated DB: 71 AEST unchanged, 71+4 ANST test records; temporary data removed and MariaDB stopped in finally/trap.
- 16 automated unit tests PASS, QA manifest 639/639, PHP lint PASS.

## Root cause and precise fix
- WP >=5.6 wp_untrash_post() gives regular restored posts status draft by default; ANST bootstrap selects publish.
- PR #310 adds only a scoped wp_untrash_post_status filter for ANST CPTs; retains previous status publish/draft/pending/private. Original AEST CPTs remain on WordPress default.
- Exact diff comparison proved only one filter added to active production PHP, preserved file mode 600.
- Production smoke: ANST prior publish→publish; ANST prior pending→pending; AEST defaults draft. Existing ANST cron pre_delete_post guard remains false for deletion while cleanup disabled.
- Production: REST authenticated GET 200; POST 423; anonymous GET 401; AEST=71 ANST=71 ANST trash=31; write/cleanup options 0.
- SHA original plugin unchanged; only new anthares-studio PHP changed.

## Pending gates
- G4 visual desktop/mobile and real browser authenticated screens STILL PENDING (existing automation profiles have no valid login).
- G5 ACF schema and migrator in PRs #308/#309 validated in isolated MariaDB but live ACF remains OFF.
- G6 navigation and G7 requirements 001–188, G8 public release not yet homologated.
- Do not enable public studio, author writes or ACF runtime until visual and full QA acceptance.
