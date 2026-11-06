# Lease — AOI 16 Instagram Buffer: inspeção individual de estado remoto
STATUS: RUNNING
AREA: cortes-instagram-buffer-readback-diagnostics
ITEMS: [16]
OWNER: ChatGPT AOI16 Instagram diagnostics 2026-11-06
DATE_UTC: 2026-11-06T21:09:03Z
LEASE_EXPIRES_UTC: 2026-11-06T21:39:03Z
BASE_MAIN_SHA: c611ce2e10d8a5aba82d31560e07ac23c6d37af1
GOVERNANCE_MANIFEST: 223433740e807a90
TARGET: tools/cortes_buffer_instagram_cloud.py
TARGET_GITHUB_BLOB_BEFORE: 12d647efa1685e62292339730c65c5e37ad9759a
TARGET_GITLAB_MAIN_BLOB_BEFORE: 12d647efa1685e62292339730c65c5e37ad9759a
BASELINE_PROVEN:
- 2026-11-06 GitHub run 42291811356 success; RECONCILE_ONLY, 0 confirmed, 0 new posts; Bitwarden auth succeeded.
- Three Instagram Buffer entries remain uncertain in Neon with buffer_scheduled evidence; four additional entries remain uncertain for other causal categories.
- Backend buffer-pending returns up to 25 eligible rows; current readback returns only count when Buffer reports a non-sent status.
- GitHub and GitLab script blobs match. The production pause must remain true.
FAILED_AVOIDED:
- No media publication, Neon ledger rewrite, Graph token reprobe or Bitwarden secret retrieval outside runner.
- No workflow dispatch or changes to workflow YAML. Preserve other agents' PRs.
SUCCESS_SIGNAL:
- Small patch reports an allowlisted outcome per pending record (sent, scheduled, failed, missing, other), omitting content, media URLs, tokens and remote identifiers.
- Verified sent Instagram links retain account, automatic mode and permalink gates; only verified posts enter Neon reconcile.
- Offline tests cover status classes and invalid identity/scheduling. Live publisher remains paused.
FAILURE_SIGNAL: Unexpected source blob/HEAD, conflicting lease, or failed checks => stop.
TEST_VALIDITY: Mocked Buffer response fixtures only; do not infer live Buffer states.
ROLLBACK: Revert the new code PR. Never mutate live queues as part of diagnosis.
COST_ADDED: R$0
BRANCH: fix/aoi16-buffer-individual-readback-20261106
LEASE_PUBLICATION: Protected main refused a direct lease commit (409); first commit on isolated feature branch carries this lease, pending reviewed merge.
