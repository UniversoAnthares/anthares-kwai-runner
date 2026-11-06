# AOI 16 — Instagram Buffer per-record remote state diagnostics
STATUS: PARTIAL; CODE_PATCH_READY
AREA: cortes-instagram-buffer-readback-diagnostics
ITEMS: [16]
OWNER: ChatGPT AOI16 Instagram diagnostics 2026-11-06
DATE_UTC: 2026-11-06
GOVERNANCE_MANIFEST: 223433740e807a90
BASE_MAIN_SHA: c611ce2e10d8a5aba82d31560e07ac23c6d37af1
LEASE: test-hub/findings/lease-cortes-instagram-buffer-diagnostics-20261106-2109.md
LEASE_STATE: CLOSED_UPON_THIS_FINDING; proposed patch remains in PR until merged
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2132
BASELINE_PROVEN:
- GitHub Actions run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42291811356 = completed/success; readback mode selected, 0 new posts, 0 confirmations.
- Neon previously read-only: 128 confirmed, 238 queued, 7 uncertain; 3 of the 7 have Buffer remote IDs and buffer_scheduled evidence.
- Bitwarden Secret Manager key retrieval succeeded in existing workflow; credentials not revealed.
- Neon queue buffer-pending selects up to 25 buffer_scheduled uncertain rows, including three existing Instagram records.
FAILED_AVOIDED:
- No new publication, workflow dispatch, editing queue/Neon, token exposure, Graph 401 retry or user PC execution.
IMPLEMENTED_IN_PR:
- New inspect_buffer_post reports allowlisted Buffer states, missing and other, per record; retains identity/account/scheduling/permalink validation.
- Only verified sent+valid link reaches queue('reconcile'); records without verified evidence stay uncertain.
- Logs use short ledger ID suffix and state; no account secrets, source media or public permalink.
- Workflow job now requires pause variable explicitly 'false' for ordinary publish; unset fails closed.
- RECONCILE_ONLY sets ANTHARES_SOCIAL_COMMIT=0 so Buffer createPost remains disabled on reconciliation jobs.
- New unit tests in tests/test_cortes_buffer_instagram_readback_diagnostics.py; nine test methods added.
TEST_VALIDITY:
- Isolated Python fixture duplicated the changed functions; ast.parse PASS, eight mocked behavior tests PASS (8/8). This verifies extracted logic, not the complete repository module.
- Repository CI/test execution has not been observed yet; not PRODUCTION_PROVEN.
SUCCESS_SIGNAL:
- A governed merge with passing relevant checks, followed by a separately authorized reconcile_only run that emits one REMOTE_POST_STATE per pending Buffer record.
NEXT_ALLOWED_OPERATION:
- Review/merge PR #2132 if repository gates permit; retain PAUSED=true. Run reconcile_only after merge with no publication, collect status and independently verify any sent permalink before accepting Neon receipt. Keep four non-Buffer uncertain rows quarantined.
COST_ADDED: R$0
ROLLBACK: revert PR via normal review/merge. No deployment or queue write occurred in this patch.
