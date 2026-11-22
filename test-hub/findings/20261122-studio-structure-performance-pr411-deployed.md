# STUDIO structure selector performance — PR #411

Date: 2026-11-22. Owner GPT6/STUDIO_STRUCTURE_PERF_20261122. Lease test-hub/findings/lease-studio-structure-performance-20261122.md CLOSED_SUCCESS.

## Scope and fix
- User report: selection of a narrative structure on anthares.us/studio froze or seriously slowed the tab.
- Root causes in client: indiscriminate subtree MutationObserver producing repeated layout reconciliation, non-idempotent chapter card rearrangement for partial Hero Journey stage orders, full-root rerender on model selection, and eager chapter select rendering for every stage.
- Corrections: observer reacts to mount point additions/removals only, coalesced once per animation frame; card ordering is idempotent even when configuration partial; model switch replaces only .aest-structure panel; chapter select options generated lazily when details expand.
- Model state / previous chapter classifications remain in WordPress. /estudio/ legacy left unchanged.

## Audit
- Repository UniversoAnthares/anthares-wordpress PR #411 merged as 826cbe76f91221676905d0315abc72e4e0bce691.
- PHP WordPress rollback QA: 46/46 PASS (qa_structure_models_transaction.php), ROLLBACK=EXECUTED, 9 models and switching, stable chapter IDs, ownership isolation.
- Python contract: 11/11 PASS (test_narrative_timeline_contract.py). Manifest preflight: 761/761 PASS. V8 JS parsing: 2/2 PASS.
- Production CAS before replace: estudio.js ec969735b394045b8dbb46ff1ad87274a4176acb; timeline.js 9dbbbe8f1907cbc2c0e2df97b82f98f1dadae55a.
- Production new blobs: estudio.js 7ee0f63d93462312ba05875604269a2c01dc7535; timeline.js 97408666bbff2ed9756825fa1fe5376291e4416f.
- HTTP/CDN readback with cachebuster exactly matched both new Git blobs. /studio/ HTTP 200 and /estudio/ HTTP 200.
- Private rollback backup: /home/u566597497/domains/anthares.us/studio-private-backups/20261122-structure-perf-pr411. /estudio/ legacy file blob remains e4a9812ac21b5c977b93e53fe65131b43e23ba85.
- Remaining: authenticated hands-on GUI, accessibility and device-size verification; refresh existing tab to load updated JS.

No user project, manuscript, timeline or private beta data was edited during publication. All QA DB writes rolled back.
