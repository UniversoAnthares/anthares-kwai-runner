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

### Final static QA of current branch

At WordPress branch commit `ce8214af0dbf90503c546edabc8764b4f9d5581a`, source static contract 12/12 checks PASS: trash GET has no purge/hard delete; board GET has no meta update; pilot admin guard present; ACF default OFF; history preserves URL on save failure; Quill expected content hash; tests for trash GET, board GET, history save failure, and frontend handlers are present; manifest mirrors match. Tracked QA inventory: **665/665**, zero missing, zero duplicates, zero extras.

**Scope of evidence:** source-only checks. The newly added tests have NOT been run as a full Python suite at this branch HEAD. The installed earlier 13/13 Python suite and 3/3 JS simulated behavior were run separately; never aggregate them into a single green PR acceptance result. The trash GET patch remains code-only because the authorized staging invocation received a security refusal. Deployed cleaning flag `anst_trash_cleanup_enabled=0` remains the protective control.

## Additional operational changes (17 Nov, ~14:41–15:05 America/Campo_Grande)

- **GET Trash pure read**: Removed the destructive `anst_cleanup_trash()` call from the `anst_trash_list()` GET handler. Branch code `e1de809e3f092088029ebf0608143b9745cc7b7a`; regression added `ce8214af0dbf90503c546edabc8764b4f9d5581a`. Deployed guarded PHP SHA256 `58d02570e39bf6a5ed7c255c4e65d3856765a6200d842606bdfe4c3703cd085f` after exact prior SHA check, PHP lint before/after, private backup; GET REST as administrator returned **HTTP 200**, **31 trash entries**, `anst_trash_cleanup_enabled=0`, unchanged cleanup timestamp (`NO_TOUCH=PASS`). Original `/estudio` preserved.
- **Chapter autosave in flight and back button**: `saveChapter()` now returns `false` when an earlier save is pending, `navigate()` and `openRouteFromLocation()` guard both dirty and busy; `back-chapters` requires successful save. JS change `a85ed498be66e3144cc013a75cf90ef271925159`; V8 runtime behavior checks 4/4 PASS.
- **Open/create chapter and structure**: Direct `chapter-structure`, `open-chapter` and `new-chapter` handlers now check for pending/failed save before changing editor content; change `378836ee3df6ff1dd0d5821f72bd93baf7c4629c`. Six V8 scenarios PASS, covering failed/successful saves for three buttons.
- **TXT reimport**: Reimport now guards `dirty||saveBusy` and retains the opened manuscript and status message when reading/importing fails; new code `8707d67fd62d1d331fbc57bdd273553283680f73`. Four simulated V8 scenarios PASS, including API failure and successful reimport.
- **Tab unload**: Added a native `beforeunload` warning for unsaved chapter or planning state (`dirty`, `saveBusy`, `unlockDirty`, `unlockBusy`). Code `cedcaa4dc749539af71b507b9ce21534c79be829`; five V8 cases PASS (saved state bypass and four pending-state variants).
- **Project creation response**: `createProject()` validates the returned numeric ID; if POST succeeds but GET details reload fails, keeps new project in local list and reports it is already saved, preventing a misleading reattempt. Code `57d7a4f718eb3db71edd8ee64e8866bb3f532ff1`; 3/3 V8 scenarios PASS.
- **Chapter creation response**: `new-chapter` validates returned ID; if a subsequent GET reload fails, shows the saved chapter ID and keeps the user in list rather than triggering a blind duplicate. Code `33c078ab427cfd5f816265f578d77035797d0cb7`; 5/5 V8 scenarios PASS.
- **Latest deployed assets**: `anthares-studio/assets/estudio.js` Git blob **`735721542467dd107913501e08d643603c29ad63`**; PHP SHA256 `58d02570e39bf6a5ed7c255c4e65d3856765a6200d842606bdfe4c3703cd085f`. Each JS change was made in a private Hostinger staging file, required to match the exact reviewed GitHub blob, with prior version backed up and atomic promotion. All jobs executed detached/invisible; no user desktop windows/restarts.
- **Latest post-deploy QA**: `python3 -B -m unittest discover -s anthares-studio/tests` 13/13 PASS; PHP8.3 lint PASS; installed asset blob exact. Read-only post-deploy CPT totals remain **AEST 71 / ANST 71** (35 projects, 13 notes, 7 chapters, 16 cards each), and options `anst_writes_enabled=1`, `anst_acf_runtime_enabled=0`.
- **Important distinction**: V8 tests exercise extracted live JavaScript functions and event handlers with fake API responses. This is valid simulation evidence, not the authenticated desktop/mobile browser journey and not an actual REST write test. The latter remain blocked as described below. No user records were created/deleted in these tests.

## Additional G4 acceptance — basic forms and the newest production JS (17 Nov, ~15:05 local)

- **Input preservation on form-submit errors:** A generic error formerly called `render()`, erasing in-progress values in planning/rename/card forms. It now attaches a `role=alert` inline message without redrawing the form and re-enables the submit button. The note-form special handler is retained. Branch code `fdc5009f3e8a6812bf6e17cfc010bc042abb8ea2`, regression `5a6518a92317ea56443aacb1ae9d03d9ca025d49`. V8 simulation with actual submit handler: **4/4 PASS** (project planning, rename, board card, note).
- **Input preservation on action-click errors:** The generic click handler also previously redrew the manuscript or unsaved planning view after a server error. It now reports the error inline via `aest-save-status` or `unlockStatus` while retaining the live editor. It still redraws ordinary non-editing views. Branch code `2a789e3c52739a8660fbd25bf9e6da64116c7922`, regression `e3e6721ca2427a9fa02881d6a0c232994ba4da81`. Actual handler simulated in V8: **3/3 PASS**.
- **Latest production JS** is the exact reviewed Git blob **`96c05ac61fa8f345a613d74fb170f99e59ba7f35`**. The new PHP remains SHA256 `58d02570e39bf6a5ed7c255c4e65d3856765a6200d842606bdfe4c3703cd085f`. The original PHP stays SHA256 `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- Both fixes deployed via private Hostinger stage, matching exact Git blobs, backups retained, and detached Session 0 jobs; no desktop interaction or reboot. **Post-deploy PHP 8.3 lint PASS, installed 13/13 Python tests PASS**, `anst_writes_enabled=1`, `anst_acf_runtime_enabled=0`.
- **Final branch QA inventory** at commit `e3e6721ca2427a9fa02881d6a0c232994ba4da81`: 665 auditable files, 665 manifest assignments, zero omissions/duplicates/extras, mirrored manifests identical. GitLab peer branch not found and was not overwritten.
- G4 C008/C009/C014/C016/C021 remain **PARTIAL** until actual authenticated UI journeys and REST write responses are observed. These operations were previously blocked by tool security and have not been retried through alternate channels.

## G4 C024/C025 and script safety: checks executed 2026-11-17 afternoon

**Read-only tenant isolation (no customer mutations):**
- Verified the two actual project owners in production (15 published projects for one author and two for the other); a GET `/anthares-studio/v1/bootstrap?project={foreign}` as another authorized account returned **404**. The owner querying that project received **200**. Exit 0 and `RESULT=PASS`. This is now a regression in the isolated DB fixture of code PR #316 (commit `5a704f5311dfeb26e9cef144dd5fe73ad98a5331`).
- GET `/anthares-studio/v1/bootstrap` as a logged-out user returned HTTP **401**. Shortcode `anst_shortcode()` rendered the login gate and omitted the private `anthares-estudio-root`; page 21383 remains `private`. `GUEST_SHORTCODE_SAFE=PASS;PAGE_PRIVATE=PASS`. This proves the indicated read-only cases, not the full web-cache/CDN matrix.

**Inline bootstrap JSON safety:** before the fix, the initial document JSON used `JSON_HEX_TAG|JSON_HEX_AMP|JSON_HEX_APOS|JSON_HEX_QUOT`, while the `window.AntharesEstudio` settings inline script omitted those flags. Patched only the new plugin, made both JSON encodings HTML-script-safe; branch commit `9afed11b3703cedf82350819f5d9a46aa00cb06c`, static regression `c8354d7075d9a5948caff97e0343341bdec620bd`. Hostinger staged PHP lint PASS, deployed with private backup and exact SHA check, then tested a script-terminator probe with `wp_json_encode`: `SCRIPT_TAG_SAFE=PASS`. Intermediate plugin SHA256: `66ea7fbcc35d7bab32ae7b512461a6efb3f05384810a693284f89ed8816ecee6`. Live installed Python tests 13/13 PASS.

**G4 shared writing guard reconciliation:** live PHP had a narrower inline `anst_permission()` guard (non-admin returned 423 for both unauthorized and disabled writes), whereas PR #316 implements the shared `anst_write_pilot_gate()` with semantically correct status 403 for restricted nonadmins and 423 for disabled writes. Replaced *only* that narrow guard and the `anst_lesson_permission()` rule in live new-plugin PHP after a staged lint and expected-SHA validation, preserving backup `~/.anthares-studio-backups/anthares-estudio.php.before-pilot-gate-20261117`. **Current live PHP SHA256: `abb62797f3f3cf1ed6e32acaf45bfade3fbc5a75d1effb666ad6bf93e699968b`.** No changes to the legacy plugin or underlying user records.

Post-deploy actual WP-CLI permission tests used *no POST mutation* (in-memory permission checks): `ADMIN=ALLOW`, `LESSON_ADMIN=ALLOW`, `NONADMIN=anst_pilot_admin_only` (403), `LESSON_NONADMIN=DENY`, virtual flag disabled `anst_staging_locked` (423), stored writes flag remained `1`. Live ACF remains OFF; plugin remains private. Legacy plugin SHA256 baseline `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.

All these operations ran in detached Session 0 jobs and completed; no desktop windows, interactive user input or reboot. Security denials affecting authenticated-browser reading and real REST mutations remain in place; these checks did not try to bypass them.

## Remaining blockers and conditions

- Tool safety **explicitly blocked** the command for real REST create/edit/delete smoke with temporary records and cleanup; no attempt was made to bypass through another channel. Consequently full CRUD functionality C001-C025 cannot be declared approved.
- Browser tool rejected reading the authenticated /studio tab due an unavailable browser security check, warning against indirect workarounds; no alternate attempt to read that protected tab. Desktop/mobile visual comparison with /estudio remains pending.
- Production PHP is a narrow guarded hotfix and differs from the fuller feature-flag implementation in draft PR #316; the branch is **unmerged**, and its final Python suite has not been executed on the branch. Deploy full PR only after standard source sync and QA.
- Whole-database isolated MariaDB instance restoration not proven because the Hostinger MariaDB install scripts could not find its files and temporary symlinks were forbidden; temporary-table restore did pass.
- Keep Studio page 21383 private; leave original /estudio and legacy user data unmodified. Continue G4 visual/CRUD parity before G5/G6 final merge and G7 expansion.
- All Windows execution used detached background jobs in Session 0, checked independently, with no user desktop windows or input, and job processes exited. No PC restart.

ROLLBACK: `wp option update anst_writes_enabled 0` (immediate write lock), then replace new-plugin PHP from private pre-patch copy if needed. Original plugin remains untouched.
