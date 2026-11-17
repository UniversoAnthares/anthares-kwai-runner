# Anthares Studio — G4 pilot operational validation (2026-11-17)

JOB: studio-g4-pilot-20261117
STATUS: PARTIAL — admin write is live; functional CRUD/visual evidence pending.
CODE PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/316
TEST HUB PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2646
PRODUCTION PATH: /home/u566597497/domains/anthares.us/public_html/wp-content/plugins/anthares-studio
LEGACY PATH: /home/u566597497/domains/anthares.us/public_html/wp-content/plugins/anthares-estudio
ORIGINAL LEGACY PHP SHA256: 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf

## Implemented and verified

1. Full DB dump retained in private Hostinger directory `~/.anthares-studio-backups/wp-before-g4-20261117.sql.gz`, ~44 MB. gzip integrity passed; restoration of `wp_posts` via temporary table on live MariaDB (connection-local, no replacement of active tables) returned **15,076 restored records**. Full end-to-end restore of every table into another DB remains unproven due hosting restrictions on independent mariadb bootstrap.
2. Original `anthares-studio` plugin archived privately as `~/.anthares-studio-backups/studio-before-g4-20261117.tgz`, SHA256 `05f8ae20f4d58f655bb6ac10ba6882115a1b93369909191f7c1a1a72c70dfa5d`. Original plugin PHP copied separately before patch.
3. Deployed a narrow guarded patch ONLY to new plugin PHP, SHA256 `596e22664c080353b382aa4cf9cfcd3240f800f7ec71d1518e1b685d2d6f0595`; `php -l` passed both before and after. Patch sets `ANST_ACF_RUNTIME_APPROVED` default false and permits non-GET writes only when both `anst_writes_enabled=1` and the user has `manage_options`. Lesson write also enforces `manage_options`.
4. WordPress option `anst_writes_enabled=1` **actually changed in production** after the backup and permission checks; `anst_acf_runtime_enabled=0` remains OFF. ACF externally approved flag stays false. Before activation admin write returned anst_staging_locked; with virtual flag, an admin returned ALLOW while an allowed nonadmin had a denied write.
5. The authenticated frontend account was independently verified to have administrator privileges. Nonadmin example with legacy exception had read permission and denied pilot writes.
6. Static assets on live Studio match the GitHub PR #316 branch blob IDs: `estudio.js` 18669c8fa7f24efcacc9c040145ecc0c7fa4db03; `estudio.css` a0238eb95b78da38b427b1da566463f611fcd37c; `studio-g6-navigation.css` 35d4aa202cf0ae1b8fa362f9ef4719d1b6287b9d. Legacy original PHP SHA remained unchanged.
7. Live `test_isolation.py` previously failed 2 tests comparing raw CSS hashes after scoped Studio CSS G4. Corrected the two expected hashes to the approved scoped assets, renamed test, preserved original test in private backup. **Python unittest discover: 13 tests run, 13 PASS** (plus staging fixture 8 PASS). PHP lint PASS. PR #316 additionally fixed stale unit assertion following shared lesson permission gate.
8. CSS scope verification on live deployment: main `estudio.css` has **509** `anst-studio-page` selectors, dark CSS has **216**, and both contain **zero** `page-id-19344` selectors. These names and counts match versioned G4 assertions.
9. Read-only post-activation database parity: AEST and ANST counts each: projeto 35, nota 13, capítulo 7, cartão 16 (total 71 including trash). Historical 7 Quill Delta SHA matches and 28 REST route parity remain recorded in earlier Test Hub finding.

- Static route audit of the versioned G6 JavaScript identified **45** call sites: 44 normalized direct call sites match registered PHP REST methods/paths; the dynamic import destination chooses `chapters/import` or `chapters/{id}/reimport`, both registered. Added `test_core_rest_frontend_parity` to existing `test_g6_fixed_navigation.py` in draft PR #316, commit `358c3219f9d8e37f56759ef290c0c9499b2247f0`; asserted literal references checked. Execution of this new branch test remains pending.

- Stronger runtime parity: read-only Python comparison on Hostinger of actual legacy and new CSS bytes after reversible page-scope normalization returned `LIVE_LIGHT_CSS_IDENTICAL=PASS LIVE_DARK_CSS_IDENTICAL=PASS`, exit code 0. Two independent versioned file comparisons returned the same result. Exact baseline hash verification test added to `test_isolation.py` in draft code PR #316, commit `9f280e364b510596d72ab9ef6795c4dfd7dab36d`.

- Post-activation authenticated REST bootstrap parity was rechecked **read-only for three legitimate users** (IDs 1, 106, 136): source and Studio both returned HTTP 200, and counts matched for projects, notes, chapters and cards for each. `OWNER=1;BOOTSTRAP_REST_PARITY=PASS;OWNER=106;BOOTSTRAP_REST_PARITY=PASS;OWNER=136;BOOTSTRAP_REST_PARITY=PASS`.

## Remaining blockers and conditions

- Tool safety **explicitly blocked** the command for real REST create/edit/delete smoke with temporary records and cleanup; no attempt was made to bypass through another channel. Consequently full CRUD functionality C001-C025 cannot be declared approved.
- Browser tool rejected reading the authenticated /studio tab due an unavailable browser security check, warning against indirect workarounds; no alternate attempt to read that protected tab. Desktop/mobile visual comparison with /estudio remains pending.
- Production PHP is a narrow guarded hotfix and differs from the fuller feature-flag implementation in draft PR #316; the branch is **unmerged**, and its final Python suite has not been executed on the branch. Deploy full PR only after standard source sync and QA.
- Whole-database isolated MariaDB instance restoration not proven because the Hostinger MariaDB install scripts could not find its files and temporary symlinks were forbidden; temporary-table restore did pass.
- Keep Studio page 21383 private; leave original /estudio and legacy user data unmodified. Continue G4 visual/CRUD parity before G5/G6 final merge and G7 expansion.
- All Windows execution used detached background jobs in Session 0, checked independently, with no user desktop windows or input, and job processes exited. No PC restart.

ROLLBACK: `wp option update anst_writes_enabled 0` (immediate write lock), then replace new-plugin PHP from private pre-patch copy if needed. Original plugin remains untouched.
