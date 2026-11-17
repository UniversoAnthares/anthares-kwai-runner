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

## Continued G4 validation — 17 Nov 2026

- The old `anst_board_columns_read()` had a read-side database update for historic default labels. Although the current database has 35 new-plugin projects, only 3 boards with stored metadata and **zero legacy default-label boards**, the side effect was eliminated in PR #316. The GET response retains the same labels and column IDs. GitHub commits: `477125033ec691d315446f66a3386dd7fb95f047`, unit test `a1016a5569da2238da8746a7cc5d62e335041237`.
- Deployed the equivalent narrow pure-read patch only into the live `anthares-studio/anthares-estudio.php` using atomic replacement and strict old/new SHA verification. New live SHA256: `daee8f582e8bf0a459451d330361431182bfbffd5d42a5d56d88e7ced6fdeff9`. Live `php -l`: PASS; live pre-existing Python suite: **13/13 PASS**; options `anst_writes_enabled=1`, `anst_acf_runtime_enabled=0`.
- Previous live PHP was retained at private `~/.anthares-studio-backups/anthares-estudio.php.before-pure-read-20261117`. The legacy `/estudio` plugin was not changed.
- Audited new-plugin current WordPress REST registration: **28 unique paths, 33 route definitions, zero incorrect permission callbacks**. All new-project mutation routes use `anst_permission`, and the lesson route uses `anst_lesson_permission`. No write requests were issued in this audit.
- Read-only current WordPress Quill integrity: **7 chapters, 7 valid Deltas, 7 contentHash matches, zero mismatches**, confirmed by WP-CLI with process exit code 0.
- Static JavaScript/UI control audit: **55 rendered actions** (including those generated by `btn()`) and **16 forms** all have a matching handler/handling branch. Added regression in existing `test_g6_fixed_navigation.py`, commits `dd79582517589d0c6d8cb16fe15b7c16c4453b89` and `b8db7a2babdbfcec2706e9fc2cf2487ddd110949`. Branch test execution still pending.
- Manifest check on current code branch: **665 auditable files, 665 assignments, 0 omissions/duplications/extras, identical manifest mirrors**. Peer GitLab lacked the branch (404), recorded as unsynced; no branch copied or reset.

## G4 acceptance C001–C025 — as verified 2026-11-17

Official basis: `ANTHARES_STUDIO_DOCUMENTACAO_20261116/06-QUALIDADE-SEGURANCA-E-TESTES.md`. A feature is PROVEN only with executed expected/observed behavior, source/deployed SHA, role, dataset and evidence. Static matching and isolated read checks count as PARTIAL when a real user journey remains untested.

| ID | Status | Verified evidence / still required |
|---|---|---|
| C001 | PROVEN | Legacy plugin PHP SHA256 `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf` unchanged; new PHP isolated. |
| C002 | PARTIAL | Both plugins active, 28 REST paths in new plugin and 33 method definitions with correct permission hooks; no comprehensive hook collision audit. |
| C003 | PARTIAL | Private page 21383 and new JS/CSS/REST registered; authenticated visual page verification unavailable. |
| C004 | PARTIAL | Original PHP unchanged and three-owner GET bootstrap parity proven; original full write journey not retested. |
| C005 | PARTIAL | Light/dark CSS byte equivalence after page-specific selector conversion proven against *installed* original; font/layout/modal screenshots missing. |
| C006 | PARTIAL | Five global entries statically match the newer approved navigation contract v2 (overrides the earlier six-entry initial gate). Interactive comparison pending. |
| C007 | PARTIAL | Seven project groups and three planning subtabs in G6 code, with old internal fragments recognized; interactive selection pending. |
| C008 | PARTIAL | Fragment/reload/back handlers in JS, test coverage prepared; actual browser history interactions pending. |
| C009 | PARTIAL | Admin POST project permission allowed with production flag 1; real project creation smoke blocked by tool safety. |
| C010 | PARTIAL | Idea note and import routes matched by JS; real note insertion/association smoke blocked. |
| C011 | PARTIAL | Card and board action/REST names verified; edit/zoom/color/drag ordering still need end-to-end tests. |
| C012 | PARTIAL | Element folders and forms have JS dispatch; creation/rename/links/versions require real writes. |
| C013 | PARTIAL | Unlock sequence functions and endpoints present; user progression/validation require end-to-end tests. |
| C014 | PARTIAL | Existing 7 chapters and hashes valid; creation, sort, structure link require real writes. |
| C015 | PARTIAL | 7 valid Quill Deltas and 7 contentHash matches; formatting/paste/Unicode/browser tests required. |
| C016 | PARTIAL | Autosave `expected_hash` and conflict checks in PHP/JS; saved/reopened content requires browser write test. |
| C017 | PARTIAL | Version snapshot/list/restore endpoints present; manual/automatic restore behavior not tested. |
| C018 | PARTIAL | Review REST/JS operations present; task/comment/status/restore real journey pending. |
| C019 | PARTIAL | 31 historical trash entries preserved per plugin and restore/cascade endpoints present; destructive/restoration tests pending. |
| C020 | PARTIAL | Original plugin/data remain unchanged in observed snapshots; create/edit in cloned CPTs cannot be certified without real write. |
| C021 | PARTIAL | Permission gate 423 and admin/nonadmin checks observed; HTTP 401/403/409/413/500 UI recovery matrix pending. |
| C022 | PARTIAL | Quill conflict guard exists; dual-browser real concurrency blocked by authenticated browser security failure. |
| C023 | PARTIAL | Mobile CSS/keyboard accessibility selectors exist; real mobile screenshots and interaction blocked by browser security. |
| C024 | PARTIAL | 33 route permission hooks correct, authenticated read counts match three accounts, allowed nonadmin denied writes; cross-owner negative response remains untested. |
| C025 | PARTIAL | Page 21383 is private and WordPress code requests `nocache_headers()`; authenticated network headers and HTML leakage still unverified. |

**Security controls:** Authenticated tab read was denied by the browser security check, and the requested real CRUD test command was blocked by tool safety. These operations were not repeated through alternate tools. A subsequent read-only 71-record all-meta comparison was also blocked by security settings and has not been retried. The 71-record total and 7 Delta hashes remain verified by earlier permitted, narrower diagnostics.

**Current deployed source:** Studio PHP SHA256 `daee8f582e8bf0a459451d330361431182bfbffd5d42a5d56d88e7ced6fdeff9`; original PHP hash above. `anst_writes_enabled=1`, `anst_acf_runtime_enabled=0`. Private code and SQL backups retained; G5 ACF activation, full PR integration, G7 UI and complete G4 still await their gates.

## Additional implementation: preserve text on failed navigation

**Defect:** the old `openRouteFromLocation()` awaited `saveChapter()` without inspecting the `false` return, then reset `chapterId` and rendered another screen. A failed `saveUnlock()` could propagate to its catch, which switched the view to Inicio, potentially discarding visible unsaved fields. In `navigate()`, the failed planning save also propagated to the outer handler. This affected G4 C008/C016/C022.

**Code:** patched the new Studio JavaScript to stop navigation on failed chapter save or planning save, preserve the current editor and restore the URL fragment with `window.history.replaceState()`. The old `/estudio` code and routes remain unchanged.

**Validation:** V8 in-memory tests using the actual versioned JavaScript passed **3/3** (chapter save failure during browser navigation, planning save failure during browser navigation, planning save failure during menu click). Full new file syntax compiled successfully in V8. Branch JS Git blob `40fb188fdd0654ce59c60472b5159b0b8678852c`.

**Deployment:** updated only `anthares-studio/assets/estudio.js` on the Hostinger. Pre-deploy original blob `18669c8fa7f24efcacc9c040145ecc0c7fa4db03` was backed up to `~/.anthares-studio-backups/estudio.js.before-navigation-safety-20261117`. A private staged file was patched and required to match the exact reviewed Git blob before atomic promotion. Post-deploy returned `G4_SAFETY_JS_DEPLOY_PASS`, exact blob `40fb188fdd0654ce59c60472b5159b0b8678852c`, a refreshed file mtime, 13/13 live tests PASS, PHP lint PASS; legacy main PHP SHA unchanged. All commands ran as hidden detached Session 0 jobs.

**Future regression:** existing `test_g6_fixed_navigation.py` extended to assert the failed-save early returns, URL restoration and safe menu transitions. Code commit `23935824990f2ef691790311709d1e9b0ac81674`. Manifest coverage after this commit: 665/665, identical mirror manifests and zero unassigned/duplicate paths. This is verified by versioned static check and runtime V8 simulation; full authenticated-browser acceptance remains pending due the existing security denial.

## Safety patch prepared — trash GET remains non-destructive (code only)

**Found:** `anst_trash_list($req)` invokes `anst_cleanup_trash()` before a read response if the opt-in cleanup setting and elapsed-time condition are both true. That would make opening the trash screen trigger a deletion. Hostinger currently has `anst_trash_cleanup_enabled=0`, so the destructive branch is disabled for the live pilot.

**Changed in branch only:** source commit `e1de809e3f092088029ebf0608143b9745cc7b7a` removes the cleanup invocation from the GET handler, preserving the scheduled cleanup and trash restoration routes. Regression `test_trash_list_does_not_delete_on_get` added to `anthares-studio/tests/test_isolation.py`, commit `ce8214af0dbf90503c546edabc8764b4f9d5581a`. Branch HEAD `ce8214af0dbf90503c546edabc8764b4f9d5581a` at this finding.

**Deployment blocked:** a staging attempt through the authorized hidden job tool was explicitly refused by OpenAI security. No alternate channel or workaround used. The live PHP remains SHA256 `daee8f582e8bf0a459451d330361431182bfbffd5d42a5d56d88e7ced6fdeff9`, with the old GET code. Mark C019 PARTIAL, deploy of this fix BLOCKED, and retain the cleanup setting OFF. Do not represent the branch code as production-installed.

## Changes to C008/C016/C019

C008 and C016 have stronger internal test and deployment evidence: an actual JS update now keeps the editor on failed navigation, and three V8 simulations passed; browser click/reload tests remain pending. C019 adds a non-destructive GET protection **in PR #316 only**; its deployment was security-blocked.

## Remaining blockers and conditions

- Tool safety **explicitly blocked** the command for real REST create/edit/delete smoke with temporary records and cleanup; no attempt was made to bypass through another channel. Consequently full CRUD functionality C001-C025 cannot be declared approved.
- Browser tool rejected reading the authenticated /studio tab due an unavailable browser security check, warning against indirect workarounds; no alternate attempt to read that protected tab. Desktop/mobile visual comparison with /estudio remains pending.
- Production PHP is a narrow guarded hotfix and differs from the fuller feature-flag implementation in draft PR #316; the branch is **unmerged**, and its final Python suite has not been executed on the branch. Deploy full PR only after standard source sync and QA.
- Whole-database isolated MariaDB instance restoration not proven because the Hostinger MariaDB install scripts could not find its files and temporary symlinks were forbidden; temporary-table restore did pass.
- Keep Studio page 21383 private; leave original /estudio and legacy user data unmodified. Continue G4 visual/CRUD parity before G5/G6 final merge and G7 expansion.
- All Windows execution used detached background jobs in Session 0, checked independently, with no user desktop windows or input, and job processes exited. No PC restart.

ROLLBACK: `wp option update anst_writes_enabled 0` (immediate write lock), then replace new-plugin PHP from private pre-patch copy if needed. Original plugin remains untouched.
