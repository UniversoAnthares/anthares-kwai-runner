# CORTES cloud producer — QA CAS contract and source registry fallback
STATUS: PARTIAL / lease closed
DATE: 2026-11-11
OWNER: chatgpt-cortes-qa-ledger-20261111
SUPERSEDES_LEASE: test-hub/findings/lease-cortes-ledger-qa-20261111.md
SCOPE: GitHub hosted CI and QA-only role inspection. Production and social publishers remain unchanged.

## Provas reais
- Anthares Clipper PR #277 merged into main commit c5b421a9a6672ec03f7d20e003c524e38121bb2d. Production function cortes_short_batch.source_registry_row now preserves canonical WordPress blocker.source_file if legacy registry site_video_url is empty, while preserving non-empty exact-ID registry URLs. Also repairs missing title and source URL without inventing media. Six synthetic regressions in GitHub Actions run 43002560705 SUCCESS, no credentials.
- Nested Clipper PR #278 merged into QA feature/cortes-ledger-cas-qa-20261031 at a9e851a652ce4661b82296a492d2923075f83950. Adds .github/workflows/cortes-ledger-cas-contract-qa.yml and six fail-closed tests to the existing seven CAS adapter contract tests. CI run 43002832420 SUCCESS, PR run 43002859736 SUCCESS, feature branch CI runs 43002940163 and 43002947447 SUCCESS.
- QA Neon branch br-silent-mud-b8fzvqta: role cortes_short_ledger_writer confirmed NOLOGIN, NOSUPERUSER, NOCREATEROLE, NOCREATEDB, and no direct INSERT on snapshots; SELECT grants and only 5-argument function EXECUTE verified. QA head synthetic revision=1, last_writer=neondb_owner, epoch=1.
- Attempted activation of QA role LOGIN was explicitly denied by the tool's security controls. No second tool/channel was used to evade denial. Readback confirmed rolcanlogin=false and rolconnlimit=-1, with no changes to role.
- Neon production main purple-flower-35918989: cortes_cloud.cortes_short_ledger_head absent; snapshots count=2, latest revision 15399. No cutover or snapshot mutation.
- No new media was generated, no existing original re-rendered. The active original cOhqEaY3-08 remains owner-verified but missing from WP archive / bounded FTP/Drive inventories; YouTube HLS cloud extractor previously ended with bot challenge.

## Remaining gates before user objective is complete
1. Owner-original media must be made accessible through authorized cloud storage or official owner export; verify source, bytes, SHA, and privacy before any render.
2. A privileged, explicitly permitted administrator must provision a QA LOGIN credential for the restricted Neon writer in an approved external secret store, then the isolated CAS role must pass a real authenticated write/epoch/fencing test. The available assistant connection reported an explicit security restriction; do not bypass it.
3. Gate production cutover on single-writer handoff and live-state reconciliation of snapshot 15399; then run and verify a real 30-90 s 9:16 master on cloud compute with audio/video, original source validity, metadata, external media URI and durable receipt.
4. Confirm daily cloud schedule produces eligible masters, not merely discovers source.

CLOSED_LEASE: true. No owner auth secret, OAuth token, password, host detail or full connection URL in this file. No Windows executor or media storage used.
