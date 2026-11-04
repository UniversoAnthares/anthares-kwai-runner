# Lease — reconciliação Kwai 68 / QA de assinatura real Node (AOI 21)
STATUS: RUNNING
AREA: kwai-uncertain-reconciliation/independent-readback-qa
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T14:40:13.801Z
LEASE_OWNER: chatgpt-reestruturacao-cortes-20261104
LEASE_EXPIRES: 2026-11-04T15:00:13.805Z
BASE_HEAD: 9d1200641d575c33286738c899a6dd455a90d7a5
TARGET_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2057
TARGET_PR_HEAD: f7da4eeb27c53b46acefd7c6ae0f806ab8a1692c
TEST_SOURCE_BLOB: e3fe38816aa5f478b4ba40fbec09efc68708ea5c
GOVERNANCE_MANIFEST: 223433740e807a90
RUN: sandbox-isolated-node-v22
JOB: none
SUPERSEDES: 20261104-kwai-independent-confirmation-staged-lease-closed.md

BASELINE_PROVEN: Kwai public profile URL yields no post URLs via free read-only fetch; search found no precise post links. Neon approved read-only SELECT observed 456 confirmed, 68 uncertain (no queued/leased/started); profile page alone is insufficient evidence of the 68. Existing PR #2057 remains draft/default-off, no producer or publisher deployment.
FAILED_AVOIDED: do not re-run a denied Neon aggregate probe; do not retry/upload any UNCERTAIN; do not enable production flag or alter queue/Neon/Cloudflare; no costly TinyFish automation (wallet negative); preserve peer PR #229.
SUCCESS_SIGNAL: offline 7/7 Node real crypto tests for PR #2057 confirmation-gate excerpt, with keys synthetic and mock SQL; append-only finding, keeping 68 RECONCILE_REQUIRED.
FAILURE_SIGNAL: wrong account accepted, HMAC bypass, invalid fence accepted, unexpected SQL calls, changing SHA or active lease conflict.
TEST_VALIDITY: reconstructed excerpt from reviewed PR head, NOT the full repository source and NOT integration test. No GitHub Actions, physical Android, media publication, or database mutation.
ROLLBACK: revert documentation only; no production effect.
