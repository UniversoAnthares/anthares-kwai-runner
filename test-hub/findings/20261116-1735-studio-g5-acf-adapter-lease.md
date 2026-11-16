# Anthares Studio — preparo de adaptador ACF e teste em banco isolado
STATUS: RUNNING
AREA: studio-g5-acf-adapter-offline
DATE: 2026-11-16
START_UTC: 2026-11-16T17:35:00Z
EXPIRES_UTC: 2026-11-16T18:35:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-acf-adapter-offline-20261116
SOURCE_BRANCH: feat/studio-g5-acf-schema-contract-20261116
SOURCE_SHA: 1d812fbd5ba45f4da364c22ef50d0e98a5802022
SOURCE_GOVERNANCE: REGRAS-OBRIGATORIAS.md SHA 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
SOURCE_AGENTS: anthares-wordpress/AGENTS.md SHA 3c61acbb2356439f927449e0824a6926be6ea959
GATE: G5 preparatory adapter, no data mutation in production

PERMITTED:
- Add new include/test files under anthares-studio/includes/acf and anthares-studio/tests in isolated branch derived from PR #308.
- Write offline ACF migrator and CLI dry-run, choose stable ACF field keys, validate historical legacy mapping and hooks.
- Test application on isolated restored WordPress+MariaDB via non-network socket and private temporary storage. Record SHA/counts/Delta, idempotency and cleanup.
- If full isolation cannot be tested, keep PR draft and flag blocking issues.

PROHIBITED:
- Alter original anthares-estudio, deployed clone PHP/JS/CSS, site visibility, user permissions, REST write toggle or ACF data in production.
- Merge PR #308 into main or turn active=false groups on before G4 visual acceptance.
- Persist artifacts in personal PC or create internet-exposed staging.
- Bypass private page access or generate privileged browser sessions.

SUCCESS:
- Tested ACF read/migrate script with --dry-run default and guarded --apply only against isolated DB.
- Legacy _anst_* values and 7 Quill Delta contents byte-for-byte unchanged; 71 posts+31 trash retained.
- Repeat apply returns skipped/zero new values, fingerprint and provenance unchanged.
- QA manifest and PHP lint, unit tests PASS; PR draft with no deploy.
