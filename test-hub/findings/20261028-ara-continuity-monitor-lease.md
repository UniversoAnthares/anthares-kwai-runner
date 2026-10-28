# ARA item 6 — external OAuth monitor without frequent Neon wake
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / github-continuity-monitor
DATE: 2026-10-28
OWNER: ChatGPT GPT-6
RUN: none
JOB: none
COMMIT: 276cb3681c96ac62d24b80e915bc403937d02367
SUPERSEDES: none
LEASE: 30min, independent GitHub Actions monitor only, no ARA agent or concurrent reserve project writes.

## BASELINE_PROVEN
GitHub main workflow .github/workflows/ara-auth-continuity-monitor.yml blob 89a8ebac3e465b7703c31f29521b06b0b1e5b8a1; peer GitLab same blob. Every 10 minutes current workflow accesses 5 control-plane endpoints including Neon-backed Vercel /health and reserve /healthz, adding independent cold starts. Primary, secondary, Cloudflare OAuth metadata discovery GET paths verified live returning valid S256/oauth endpoints with no SQL in primary. Another SYSTEM local guard every ~5min and liveness every30s exist; preserving independent incident semantics is mandatory. Full generic QA owner cadence 12 hours.

## FAILED_AVOIDED
Never disable external alerts, OAuth scope checking, deep DB checks or original incident issue. Keep 10m metadata-only check or a modest 30m cadence; deep every12h; do not mark deep incident recovered based on shallow pass. Avoid new costs, binaries, secret changes, Neon SQL, or direct unreviewed main writes.

## SUCCESS_SIGNAL
Workflow source readback, valid YAML and output/issue guards, GitHub Actions real CI or manual dispatch reports checks; merged into default main through permitted reviewed PR and scheduled triggers active. Lightweight checks do not access Neon, deep checks retain all five original endpoints. Bad metadata opens existing incident; only deep success closes it.

## FAILURE_SIGNAL
Syntax/workflow fail, missing external OAuth metadata, false incident close, main HEAD drift or unauthorized merge. No action to cancel unrelated jobs.

## TEST_VALIDITY
PR code is not active schedule until merged to main; offline checks alone are PARTIAL. Lease closes with independent finding.
