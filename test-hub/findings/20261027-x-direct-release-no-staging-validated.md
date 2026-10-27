# X release transport — no duplicate staging
STATUS: PARTIAL
AREA: x-source-storage
DATE: 2026-10-27
COMMIT: 3976527f52cd6431ff619520e768c39cd3d50e94
SUPERSEDES: none
OWNER: Codex / x-no-duplicate-staging-20261027
LEASE_SCOPE: tools/x_local_longform_producer.py, tests/test_x_release_direct_upload.py; dedicated codex/x-direct-release-no-staging-20261027 branch only. No other owner's branch or local working tree changed.

## BASELINE_PROVEN
Existing source copied rendered video to a second local staging path before checking release assets. Source and installer read from GitHub at base 9f0d2afbc5637121d2ac5b8750b126587ded2fc6. GitLab main peer read and content equivalence checked separately; no peer mutation or failover. Test Hub README/AGENTS read; full findings tree returned 999 entries with truncated=false, no same-area later finding identified. Relevant recent X workflow runs inspected and terminal/skipped; no competing publishing test launched. Provider-native digest correspondence for six historical X assets is recorded privately; no deletion attempted by this change.

## FAILED_AVOIDED
No retry of security-refused cleanup or Kwai memory-only execution. No staging rename, copy, hardlink, file deletion, live publication or new permission. A first extra regression harness stopped before tests because a local test mirror differed from the pinned provider version; classified INVALID/NOT_TESTED, then corrected by using pinned provider test/installer content in memory. A too-large command hit the Windows command-length limit before launch; corrected without creating test files.

## SUCCESS_SIGNAL
16 new direct-release tests PASS plus 8 existing X source regressions PASS. Source candidate SHA256 equivalence verified before extra regressions. Executed in memory with python -B; no media/test files written on the PC, no provider mutations. Full source readback matched blob9c5cab3aa47ea769e4db257d04d57cc6032b7082. Upload/reuse branches use original rendered input; exact asset name, state, URL, byte count and SHA256 required. 403/429 never become release creation; creation only after confirmed HTTP404. Ambiguous upload never retried in the same attempt; later read must reconcile the fixed name.

## FAILURE_SIGNAL
Missing/foreign/ambiguous asset, wrong release, mismatch or unknown upload state blocks enqueue. No post may be used as an audit test. No claim of a real new upload in this validation.

## TEST_VALIDITY
Offline source/transport tests exercise actual helper with synthetic binary streams and mocked provider responses. Existing queue/schedule/source-window regressions preserved. No check-run existed for the candidate at inspection; local tests do not imply hosted CI ran. Release metadata semantics were observed in read-only provider inventory; a new asset upload was not performed. Rendering/scan work still needs external migration: this patch removes only the extra staging copy. Historical copies remain subject to separate review refusals.

## Rollback
Reviewed revert of this transport change before a later source cycle, preserving queue and confirmed/uncertain state. Never replay publication to test rollback.
