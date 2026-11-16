# Lease Anthares Studio — esquema ACF exclusivamente preparatório
STATUS: RUNNING
AREA: studio-acf-schema-design
DATE: 2026-11-16
START_UTC: 2026-11-16T17:13:00Z
EXPIRES_UTC: 2026-11-16T18:13:00Z
OWNER: ChatGPT — CURSO ESCRITA CRIATIVA
JOB: acf-core-fields-schema-20261116
SOURCE: anthares-wordpress/feat/studio-g3-migration-dryrun-20261116 SHA ee480a823674318a5c55c07444505a4646930713
PEER: GitLab mirror main 3c001d5fb4c955e2d6c7c604080b8021f227b901 (lags GitHub Test Hub main 5271a27368ba91121f2dd6f8418bbfbb473102bf; do not push peer)
SCOPE: new anthares-studio/acf-json/*.json, anthares-studio/docs/ACF-FIELD-MAPPING.md, anthares-studio/tests/test_acf_contract.py, synchronized QA manifest files in isolated branch only.

BASELINE_PROVEN:
- Original /estudio plugin unchanged, old post counts 40 publish + 31 trash.
- Clone /studio private; 71 posts mapped, 7/7 Delta byte-for-byte parity and REST 17 active projects parity for two owners; data write toggle OFF.
- ACF 6.8.11 active, ACF Pro inactive.
- Historical clone fields use private _anst_* keys, which conflict with ACF companion references if names reused.
- G1/G4 complete visual regression still outstanding.

SUCCESS_SIGNAL:
- Valid ACF Local JSON schema with fixed group/field keys and one-to-one ledger of legacy domain fields.
- Use independent studio_* ACF field names to prevent clobbering current _anst_* legacy data.
- Test all legacy metadata assignments and no collision, QA manifest exact coverage, PHP/JS visual assets unchanged.
- PR DRAFT, no merge/deploy; future registration/write via update_field after G4 approval.

FAILED_AVOIDED:
- Directly applying ACF to live _anst_* fields, which would overwrite stored Delta and references.
- Dynamic ACF field names for per-project user zoom; use explicit user-level index map in future migration.
- Replacing or refactoring old plugin, changing page visibility, activating options or publishing user content.
- Editing existing PHP/JS/CSS or PRs owned by other agents.

FAILURE_SIGNAL:
- Unknown meta key without mapping or technical exemption, duplicate ACF field key, current branch/head drift, any change to production or source, invalid ACF JSON.

TEST_VALIDITY:
- ACF schema and tests on PR only, no runtime load or data mutation. Final gate acceptance blocked by G4 visual and migration/ACF integration.
