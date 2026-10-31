# OTIMIZAÇÃO — QA P0 elimina incidentes falsos originados de workflows não publicadores
STATUS: RUNNING
AREA: architecture/qa-p0-incident-remediation
DATE: 2026-10-31 UTC
RUN: none
JOB: none
SUPERSEDES: none
LEASE: candidate branch only, production ownership unclaimed; older 2026-10-30 five-minute watchdog and 2026-10-29 controller 30min leases expired, revalidate before promotion.
BASELINE_PROVEN: GitHub main 7a44b8c64f83fd4498d81c18d3d773424a844467; same blobs GitLab for router/watchdog/test. Public open issues #1994 (Buffer - Cloud Channel Identity Audit), #1995 (CORTES TikTok P0 immediate cloud recovery), #2000 (CORTES independent cloud round watchdog), #2005 (CORTES Clipper hosted migration preflight), #1992 (TikTok uncertain read-only forensic audit) were incorrectly promoted as publisher failure P0.
HYPOTHESIS_CAUSAL: QA publisher monitoring uses broad name tokens, so it includes failed diagnostic, preflight, recovery and watchdog workflows, generating extra P0 issues and potential extra executor Actions.
IMPLEMENTED_CANDIDATE: matched exclusions in tools/cortes_qa_p0_router.py and the hosted cloud alert JavaScript in cortes-qa-p0-publication-watchdog.yml. No scheduled cadence changed. Existing real publisher names, e.g. CORTES TikTok Neon Producer, retained. Explicit unit cases protect both paths. Existing Threads identical-fingerprint 12h guard of 20261029 preserved.
FAILED_AVOIDED: no incident closure, job cancellation, reset, CI dispatch, publication, Windows change or external API test.
SUCCESS_SIGNAL: directed offline tests pass; five observed nonpublisher names excluded in both routes, actual publisher failure still included; subsequent production run emits no new P0 for these diagnostic classes while detecting true publisher failures.
FAILURE_SIGNAL: real publisher failure is excluded, missed authentication failure, loss of immediate incident delivery, differing backend classification; revert via PR with current SHA.
TEST_VALIDITY: new candidate unmerged; source regression only. CI/run evidence pending external scheduler availability. GitHub kwai-runner last observed Actions run 2026-10-30T21:13:53Z despite 2026-10-31T03:50Z remote heartbeat.
COST: zero new services; projected reduction of accidental incidents and downstream diagnostic dispatches, not yet quantified.
ROLLBACK: revert only source classification changes in router and cloud watchdog plus regression test with optimistic concurrency; preserve unrelated state.
AOI: associated with fixed item 16, PARTIAL pending live readback. Related schedule candidate PR #2014 is independent and remains draft.
