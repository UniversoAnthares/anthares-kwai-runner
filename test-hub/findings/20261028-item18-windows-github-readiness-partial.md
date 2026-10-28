# Item fixo 18 — Windows/GitHub, prontidão segura comprovada; takeover produtivo pendente
STATUS: PARTIAL
AREA: architecture/windows-github-publication-contingency
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40789291185
JOB: 123170204928
COMMIT: f309d0d56f384c07c2b83bb2a6d668bb71dbc928
SUPERSEDES: 20261028-item18-windows-github-contingency-readiness-running.md
LEASE: CLOSED — read-only acceptance and minimal source hardening complete.
OWNER: AOI item18

## Evidência atual
BASELINE_PROVEN: canonical GitHub source and independent Hostinger Forgejo recoverable Git/QA, prior real mirror SHA receipt GitHub run 40746611827; Windows GH fallback runners historically present, but current reachability NOT_VERIFIED.
PRE_CHANGE_RISK: BOTH Windows last-resort workflows contained `workflow_run` failure triggers. An upstream failure is not `NOT_APPLIED` and could trigger a competing upload even after TikTok accepted media.
LIVE_NEON_READBACK: read-only SELECT of `public.cortes_tiktok_publications` and `public.cortes_tiktok_lucasrosalem4_publications` on 2026-10-28 UTC: universo 414 confirmed, 88 queued, **10 uncertain** with started and no remote_id; lucas4 115 confirmed, 199 queued, **2 closed_unverified** with started and no remote_id. Lucas4 cutover control reports cloud_enabled=true, local_frozen_at historical only. No ledger row was modified.
CLOUD_WORKFLOW_READBACK: GitHub-hosted run 40789291185 job 123170204928 used Actions REST to verify BOTH Windows workflows are `active` (not disabled_manually as an older snapshot said).
COMMIT_PROOF: GitHub PR #1831 merged SHA `f309d0d56f384c07c2b83bb2a6d668bb71dbc928`. Main branch readback confirms removal of `workflow_run` in both fallback files, manual dispatch requires `proof_publish_one=true`, `diagnostic_only=false`, account-specific `TIKTOK_*_WINDOWS_TAKEOVER_APPROVED=true` and no other cloud primary.
TEST_VALIDITY: exactly one GitHub-hosted nonpublishing workflow on pull_request: run 40789291185/job 123170204928 SUCCESS, `ITEM18_UNIVERSO_FALLBACK_FENCED=PASS`, `ITEM18_LUCAS4_FALLBACK_FENCED=PASS`, `ITEM18_SAFE_READINESS_CONTRACT=PASS`. Actual Github Actions workflow state read, no Windows runner / media / session or Neon write.
TEST_OUTPUT: `PUBLISH_WORKFLOW_ENABLED=true`, `GIT_READY=UNKNOWN` (fresh external remote readback not exercised in this run), `RUNNER_READY=UNKNOWN`, `PUBLISH_AUTH_VERIFIED=false`, `LEASE_RELEASE_PROVEN=false`, `TAKEOVER_ALLOWED=false`, `CONTINGENCY_READY=false`, `ITEM18_READINESS=PARTIAL`.
WINDOWS_READBACK: ARA command timed out; WinRemote returned an existing shell lock; MeshCentral read-only execution timed out. Windows process readiness not proved; no destructive fallback or publisher dispatch attempted.

## Gate remaining before DONE
Dimensão A (Git restore and CI): prior independent evidence is PROVEN; current integrity parity must be fresh when an actual takeover is requested.
Dimensão B (live publication): NOT_PROVEN. Require independent source failure, approved FROZEN primary, terminal source status, independent reconciliation of all started/uncertain/closed_unverified receipts, valid Neon per-account generation and account lock, authentication on the secondary, explicit owner approval, successful ordinary authorized publication by backup and independent remote confirmation, with zero competing publisher runs.
SUCCESS_SIGNAL: per-account production takeover receipt with source/target, UTC, segment_id, lease_generation, remote_id/URL, independently verified account/content, no double publish. A green no-upload CI check is not sufficient.
FAILURE_SIGNAL: any source uncertain, secondary workflow disabled, inaccurate session identity, competing lease, stale Git mirror, quota gate, or missing approval; preserve original and block takeover.
NEXT_ACTION: reconcile 10 universo uncertain and 2 lucas4 closed_unverified by independent profile evidence; validate current Windows runtime only once free and approved, then a strictly authorized live takeover after provider freeze. This scope intersects fixed items 1,3,15,16 but does not mark them done.

NO_NEW_COSTS: true
NO_WINDOWS_STAGING: true
NO_MEDIA_UPLOAD: true
NO_SECURITY_DENIAL_BYPASS: true
