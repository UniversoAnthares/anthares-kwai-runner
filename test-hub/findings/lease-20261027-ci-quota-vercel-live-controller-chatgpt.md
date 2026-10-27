# Lease — controller authenticated GitHub cancel-first on independent Vercel
STATUS: RUNNING
AREA: github / ci-quota-live-controller
DATE: 2026-10-27
RUN: none
JOB: anthares-ci-quota-controller (isolated Vercel project)
COMMIT: e2e89536ded633347a12cc3b981afdc7e0a8c3f3
SUPERSEDES: none

Owner: ChatGPT. Scope ONLY new deploy/anthares-ci-quota-controller/* and tools/ci_quota_signal_github.py, plus isolated Vercel project anthares-ci-quota-controller. No existing publicadores, no shared GitHub workflows, no social account mutation. Expiration: 30 min from creation.

BASELINE_PROVEN: production Neon table CI attempts deployed additive; login role anthares_ci_quota_limited without inherited privileges, no publication rights; Vercel project created and DATABASE_URL stored sensitive; no live cancellation yet.
FAILED_AVOIDED: broad Neon role from Neon API was deleted. Never use personal or repository-wide GitHub tokens; require cryptographically verified GitHub OIDC matching repository and exact run_id; do not send tokens to output/logs; quota structured only; no automatic fallback while uncertain.
SUCCESS_SIGNAL: Vercel endpoint deployed and accessible with DB identity, OIDC validation enforces identity before requesting cancel; code installed for existing CI jobs.
FAILURE_SIGNAL: unverified bearer accepted, job ID can differ from claim, or side-effect job is automatically resumed; keep cancel mode disabled.
TEST_VALIDITY: deployment and health readbacks prove reachability only. Cancellation real depends on an owned job producing a quota event.
