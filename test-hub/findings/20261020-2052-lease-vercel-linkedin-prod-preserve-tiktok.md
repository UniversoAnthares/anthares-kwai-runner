# Lease — Social quotas on Vercel preserving current TikTok deployment
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
RUN: none
JOB: none
COMMIT: 90c5f3175909b0ec8162ad31af7ee27ca72198c2
SUPERSEDES: none
LEASE_AREA: vercel-cortes-queue-social-quotas
LEASE_OWNER: chatgpt-current-conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T01:22:00Z

## BASELINE_PROVEN
Production project anthares-remote-primary (Vercel ID prj_YiPa15XVqZnUuNE7VtExfcjh0f3q) currently READY at deployment dpl_87aaMmBdwPMGcFnnRDyMVDhFnmT8, source SHA 90c5f3175909b0ec8162ad31af7ee27ca72198c2. Main merged PR #269 SHA 0d3aca85e0246a290f8847108dbca2f65cd12de0; repository histories diverged, with vital current TikTok 3-minute protections on production branch. The current production source file vercel-ara-primary/api/cortes-queue.mjs SHA 2c74221a52dbbe5bffb8cc8b9215d7b731067e02.

## FAILED_AVOIDED
Do not deploy main over production hotfix; preserve TikTok live queue changes. Do not reset Neon, rewrite uncertain jobs, or test via real posting.

## SUCCESS_SIGNAL
Minimal LinkedIn 20/day per-target quota patch on production baseline in isolated branch; syntax and CI valid; Vercel new production deploy from exact commit with verified health; no regressions for TikTok.

## FAILURE_SIGNAL
Change to live Vercel baseline, unexpected build/health failure, competing lease or SHA movement: halt and retain old deployment.

## TEST_VALIDITY
Static checks only on copied source. A production deployment without actual OAuth cannot establish a LinkedIn/Pinterest real post.
