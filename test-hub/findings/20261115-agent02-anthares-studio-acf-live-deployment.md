# AGENTE 02 — Anthares Studio ACF item 5 — Production deployment evidence

STATUS: PROVEN (313 field definitions deployed / 6 groups verified through live ACF; full authenticated write canary NOT_RUN)
DATE: 2026-11-15
OWNER: AGENTE 02
REPOSITORY: UniversoAnthares/anthares-wordpress
SOURCE_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/284 (merged)
MERGED_COMMIT: 30c6cbbd3f649f1860ee9fab534509df8bdc5c7e
SOURCE_COMMIT: 6f439e12209a5ac6887cb8a8f64bf7402861b15a
INTEGRATION_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/275 (remains draft)
SITE: https://anthares.us/studio/

## Scope and integrity
- Published ONLY the 12 files `anthares-studio/acf-json/group_anst_*.json` and `anthares-studio/includes/entities.php` on Hostinger production.
- Git blob SHA for deployed entities.php: `44292e508ad14cbfca586250cc112ba9261951cf`; production source and repository contents are identical (cmp PASS).
- All 12 production ACF JSON files byte-identical to source commit (diff -qr returned 0 differences).
- 313 ACF field keys in deployed Local JSON; 91 preexisting fields untouched, 222 optional additions; 12 existing groups retained.
- Backup snapshot before deployment: `~/domains/anthares.us/anthares-private-storage/studio-acf-rollback-20261115-6f439e1`. Contains `acf-json/` and previous `entities.php`. Backup original entities Git blob SHA `3ae822a7196eb1f3274949fca808d972d8d509c0`.

## Executed tests and evidence
- On Hostinger external isolated temp clone of exact commit, PHP 8.5 syntax lint PASS for entities.php, anthares-studio.php and mock QA.
- `python3 anthares-studio/tests/acf-schema-contract.test.py`: PASS, 12 groups / 313 unique keys / 91 original fields / 32 cited fields.
- `php anthares-studio/tests/acf-runtime-contract.test.php`: PASS with 34 simulated functional/security checks, including cross-project/owner isolation, invalid values, date Ymd normalization, concurrency conflict, and fail-closed incomplete schema. (Mock WordPress; not a production write test.)
- `python3 qa/manifest-coverage-preflight.py --check`: PASS; 646 auditable files assigned once.
- `python3 anthares-studio/tests/legacy-inventory-contract.test.py`: PASS.
- `php qa/anthares-orchestrator-qa.php`: PASS.
- Live ACF 6.8.11 WordPress read-only WP-CLI test: `group_anst_personagem=47`, `lugar=31`, `evento=33`, `cena=41`, `beat=20`, `fonte=21`. Types relationship, post_object, date_picker reported available.
- Production PHP 8.3 syntax lint PASS for adapter and plugin main file; site `https://anthares.us/studio/` responded HTTP 200 at 2026-11-15 17:15:59Z.
- External temporary Git clone removed; temporary WP-CLI probes removed. No content database records intentionally changed.

## Limitations
- Other six groups are present in Local JSON and 313 fields were checked in deployed files, but their live ACF field counts were not individually confirmed due intermittent SSH control-plane errors.
- Real authenticated production write/reload, transactional rollback drill and full ACF JSON save-in-admin not performed. Avoid test writes to real user data and do not assume those cases passed.
- GitHub Actions has no run for feature-branch QA; server-side offline tests are the decisive QA evidence.

## Recovery
Restore the code snapshot from the private Hostinger backup above, preserving the original paths `acf-json/` and `includes/entities.php`, then re-run PHP lint, ACF group read-only probe and site HTTP smoke. Do not modify manuscripts, user data, legacy `/estudio`, or other agents' files.
