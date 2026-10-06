# TikTok QA40 after QA30 worker contention
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-06
RUN: pending
COMMIT: 129e159a8dff5440df088c664dfa2e6c1e67978f
SUPERSEDES: test-hub/findings/20261006-1050-final-qa30-closure-dispatch.md

QA30 infrastructure observations themselves succeeded, but many identity probes were invalidated by shared Render lock contention (HTTP 409 worker busy); other valid probes timed out. Central state remained HTTP 200 with 21 cookies and status/bootstrap controls were healthy.

Per owner instruction, causal successor is expanded to 40 simultaneous reversible jobs. Important causal change: each replica no longer concurrently POSTs bootstrap-session before probing, because that mutation itself amplified lock contention. Existing bootstrapped state is observed; 30 replicas exercise bounded session-test and 10 are read-only session-status controls. No publish occurs.

HELP REQUEST: inspect QA40 distribution specifically for 409 vs timeout vs identity_verified. If 409 remains dominant, do not create QA50: implement a multi-worker/session-test pool or an isolated read-only identity verifier so concurrency is real rather than serialized behind one Render process. If any identity_verified=true appears, stop diagnostics and move to one fenced canary only.
