# AOI #16 — Instagram P0 #2044: correção causal e NOT_APPLIED do envio histórico
STATUS: RUNNING
AREA: qa-p0-instagram-2044-terminal
ITEMS: [16]
DATE_UTC: 2026-11-06
OWNER: chatgpt-aoi16-instagram-2044-terminal-20261106
LEASE: scoped to issue #2044 and this finding; 40min.
GOVERNANCE_MANIFEST: 223433740e807a90
BASE_HEAD: bf79285042633bcc8b80450ae3dcd6b268b1c0d9
PREVIOUS_FINDING: test-hub/findings/20261105-aoi16-instagram-import-rootcause-fixed-lease-closed.md
PEER: GitLab project 87307248 main scripts/instagram_autopublish.py blob d1fcd28950310b2732ddbdb5bc1e7f345a3cb432 and test-hub/test_instagram_autopublish.py blob e509dcc851673c17bfd3f17a655ae5f367b8d340; same GitHub blobs.
SOURCE_FIX: PR #2105 merged SHA ac7711074981ddf29e7fbcc82d6456a553c3f8ed.
ISSUE: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/2044
FAILED_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41258536427
FAILED_JOB: 124706765819

## BASELINE_PROVEN
On 2026-11-01 00:52:11 UTC hosted job traceback: File <stdin>, line 2 → importing scripts.instagram_autopublish → from instagram_publish import InstagramAPIError, client_from_env → ModuleNotFoundError.
The second line of the workflow inline script is from scripts.instagram_autopublish import load_ledger, save_ledger. Its first Graph publishing call client.publish_reel occurs strictly after those imports; the exception aborts before any Instagram Graph API media creation or publication in that job. This specific historical Instagram publication operation is NOT_APPLIED.
The previous Host prepared video temporarily step DID upload a Github Release asset: NOT_APPLIED refers ONLY to the Instagram Graph post, with no deletion or global no-side-effect claim. GitHub media cache handling requires separate authorization and integrity review.

## Fix and evidence
- The import is corrected to from scripts.instagram_publish import InstagramAPIError, client_from_env in source blob d1fcd28950310b2732ddbdb5bc1e7f345a3cb432.
- The regression test test_repository_root_package_import_in_clean_process tests that import in isolated Python; previous finding records positive corrected import and negative original control. No repeat testing authorized or necessary.
- PR #2105 merged as ac7711074981ddf29e7fbcc82d6456a553c3f8ed; current source matches GitLab peer.
- Workflow instagram-auto-10day.yml remains disabled_manually with zero post-patch publisher runs. Live functioning of corrected publishing pipeline remains UNVERIFIED and paused by prior explicit owner decision.

## P0 acceptance
Terminal for this historical import failure: corrected source merged + original operation NOT_APPLIED. Previous finding explicitly accepts an authenticated live-post receipt OR terminal NOT_APPLIED for the original incident. Close issue #2044 as completed with precise evidence, preserving the publisher suspension and global AOI #16 PARTIAL.
FAILED_AVOIDED: no re-enable, no media publishing, no retry, no Neon/ledger mutation, no synthetic videos, no additional tests, no cost or personal PC runner.
SUCCESS_SIGNAL: #2044 closed with causal fix and NOT_APPLIED evidence; this finding merged; publishing workflows unchanged.
FAILURE_SIGNAL: issue/source drift, security refusal, concurrent operator: stop, preserve evidence.
TEST_VALIDITY: actual previous failing hosted execution + current merged source and regression documentation; no live test needed.
ROLLBACK: reopen issue if later evidence contradicts the NOT_APPLIED proof. No media deletion.
COST_ADDED: R$0
